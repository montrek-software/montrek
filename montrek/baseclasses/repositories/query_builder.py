import datetime
from collections.abc import Collection
from typing import Any

from baseclasses.dataclasses.montrek_message import (
    MontrekMessage,
    MontrekMessageError,
)
from django.core.exceptions import FieldError, ValidationError
from baseclasses.repositories.annotator import Annotator
from baseclasses.repositories.db.hub_value_date_copy import HubValueDateCopy
from baseclasses.repositories.filter_decoder import FilterDecoder
from django.db.models import (
    BooleanField,
    Exists,
    Func,
    OuterRef,
    Q,
    QuerySet,
)


class IsTrue(Func):
    """``(<condition>) IS TRUE``, to keep an ``IN (subquery)`` from becoming a join.

    Postgres pulls an ``IN (subquery)`` that stands directly in the ``WHERE``
    up into a semi join, and picks its strategy from the number of outer rows
    it expects. Behind a dozen satellite and link joins that estimate can drop
    to a single row; the planner then chooses a nested loop and re-runs the
    subquery for every outer row. Inside ``IS TRUE`` the subquery is not pulled
    up: it stays a hashed SubPlan, run once and probed per row, whatever the
    estimate. For an ``IN`` on a non-null column the result is the same, as
    ``IS TRUE`` only differs from the bare condition on NULL.
    """

    template = "(%(expressions)s) IS TRUE"
    output_field = BooleanField()


class QueryBuilder:
    def __init__(
        self,
        annotator: Annotator,
        session_data: dict[str, Any],
        latest_ts: bool = False,
        session_start_date: datetime.datetime | None = None,
        session_end_date: datetime.datetime | None = None,
        hub_scope_pk: int | Collection[int] | None = None,
        messages: list[MontrekMessage] | None = None,
    ):
        self.annotator = annotator
        self.hub_class = annotator.hub_class
        self.session_data = session_data
        # Pass the owner's list to have the messages reach it.
        self.messages: list[MontrekMessage] = [] if messages is None else messages
        self.latest_ts = latest_ts
        self.hub_scope_pk = hub_scope_pk
        self.session_start_date = (
            self.session_data.get("start_date", datetime.datetime.min)
            if session_start_date is None
            else session_start_date
        )
        self.session_end_date = (
            self.session_data.get("end_date", datetime.datetime.max)
            if session_end_date is None
            else session_end_date
        )

    @property
    def query_filter(self) -> Q:
        request_path = self.session_data.get("request_path", "")
        filter = self.session_data.get("filter", {})
        filter = filter.get(request_path, {})
        return FilterDecoder.decode_dict_to_query(filter)

    @property
    def hub_value_date(self):
        return self.hub_class.hub_value_date.field.model

    def build_queryset(
        self,
        reference_date: datetime.datetime,
        order_fields: tuple[str, ...] = (),
        apply_filter: bool = True,
    ) -> QuerySet:
        queryset = self.hub_value_date.objects.filter(
            Q(hub__state_date_start__lte=reference_date),
            Q(hub__state_date_end__gt=reference_date),
        )
        # Scope to the hubs BEFORE annotations are built so that
        # queryset-aware subquery builders (which extract hub ids from the
        # intermediate queryset) only precompute data for these hubs.
        if self.hub_scope_pk is not None:
            queryset = queryset.filter(self._hub_scope_filter())
        if self.latest_ts:
            queryset = self._filter_ts_rows(queryset)
        satellite_aliases_dict: dict[str, Any] = {}
        for satellite_alias in self.annotator.satellite_aliases:
            satellite_aliases_dict.update(
                satellite_alias.subquery_builder.build_aliases(
                    satellite_alias.alias_name, reference_date
                )
            )
        for linked_satellite_alias in self.annotator.linked_satellite_aliases:
            satellite_aliases_dict.update(
                linked_satellite_alias.subquery_builder.build_aliases(
                    linked_satellite_alias.alias_name, reference_date
                )
            )
        if satellite_aliases_dict:
            queryset = queryset.alias(**satellite_aliases_dict)
        field_projections = self.annotator.field_projections_to_subqueries()
        linked_field_projections = (
            self.annotator.linked_field_projections_to_subqueries()
        )
        queryset = queryset.annotate(**field_projections, **linked_field_projections)
        queryset = queryset.annotate(
            **self.annotator.build(reference_date, queryset=queryset)
        )
        if apply_filter:
            queryset = self._apply_filter(queryset)
        queryset = self._filter_session_data(queryset)
        if not self.latest_ts:
            queryset = self._filter_ts_rows(queryset)
        queryset = self._apply_order(queryset, order_fields)
        return queryset

    def _apply_filter(self, queryset: QuerySet) -> QuerySet:
        """A filter that cannot be applied yields no rows: falling back to the
        unfiltered rows would pass them off as the filtered ones."""
        try:
            return queryset.filter(self.query_filter)
        except (FieldError, ValueError, ValidationError) as e:
            message = MontrekMessageError(f"Filter could not be applied: {e}")
            if message not in self.messages:
                self.messages.append(message)
            return queryset.none()

    def _apply_order(
        self, queryset: QuerySet, order_fields: tuple[str, ...]
    ) -> QuerySet:
        return queryset.order_by(*order_fields)

    def _filter_ts_rows(self, queryset: QuerySet) -> QuerySet:
        if self.latest_ts:
            return queryset.filter(IsTrue(self._latest_hub_value_dates()))
        # Use hub_id (direct FK column) instead of the hub_entity_id annotation
        # (which is itself a subquery) to avoid unnecessary nesting.
        non_null_value_date_exists = self.hub_value_date.objects.filter(
            hub_id=OuterRef("hub_id"),
            value_date_list__value_date__isnull=False,
        ).exclude(id=OuterRef("id"))
        if self.annotator.has_only_static_sats():
            filtered_query = queryset.filter(value_date_list__value_date__isnull=True)
        else:
            filtered_query = queryset.filter(
                Q(value_date__isnull=False) | ~Exists(non_null_value_date_exists)
            )
        return filtered_query

    def _latest_hub_value_dates(self) -> Q:
        """The rows that are their hub's latest ones.

        The latest rows of a hub are its rows on its newest date, or its
        undated rows if it has no dated one (see
        ``HubValueDateCopy.latest_rows``). Looked up per hub in an index
        instead of ranking every row of the table, so the cost grows with the
        number of hubs, not with the length of their time series.

        Filters applied to the outer queryset do not reach into these inner
        queries, so they cover all hubs unless a hub scope narrows them to the
        scoped hubs.
        """
        hubs = self.hub_class.objects.all()
        if self.hub_scope_pk is not None:
            hubs = hubs.filter(self._hub_scope_filter(field="pk"))
        return HubValueDateCopy.latest_rows(self.hub_value_date, hubs)

    def _hub_scope_filter(self, field: str = "hub_id") -> Q:
        if isinstance(self.hub_scope_pk, int):
            return Q(**{field: self.hub_scope_pk})
        return Q(**{f"{field}__in": list(self.hub_scope_pk or ())})

    def _filter_session_data(self, queryset: QuerySet) -> QuerySet:
        if not self.annotator.get_ts_satellite_classes():
            return queryset
        end_date = self.session_end_date
        start_date = self.session_start_date
        return queryset.filter(
            (Q(value_date__lte=end_date) & Q(value_date__gte=start_date))
            | Q(value_date__isnull=True)
        )
