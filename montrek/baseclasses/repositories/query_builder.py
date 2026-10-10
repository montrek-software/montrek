import datetime
from typing import Any

from baseclasses.dataclasses.montrek_message import (
    MontrekMessage,
    MontrekMessageError,
)
from django.core.exceptions import FieldError
from baseclasses.repositories.annotator import Annotator
from baseclasses.repositories.filter_decoder import FilterDecoder
from django.db.models import (
    Exists,
    F,
    OuterRef,
    Q,
    QuerySet,
    Window,
)
from django.db.models.functions import Rank


class QueryBuilder:
    def __init__(
        self,
        annotator: Annotator,
        session_data: dict[str, Any],
        latest_ts: bool = False,
        session_start_date: datetime.datetime | None = None,
        session_end_date: datetime.datetime | None = None,
        hub_scope_pk: int | None = None,
    ):
        self.annotator = annotator
        self.hub_class = annotator.hub_class
        self.session_data = session_data
        self.messages: list[MontrekMessage] = []
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
        # Scope to a single hub BEFORE annotations are built so that
        # queryset-aware subquery builders (which extract hub ids from the
        # intermediate queryset) only precompute data for this hub.
        if self.hub_scope_pk is not None:
            queryset = queryset.filter(hub_id=self.hub_scope_pk)
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
        try:
            queryset = queryset.filter(self.query_filter)
        except (FieldError, ValueError) as e:
            self.messages.append(MontrekMessageError(str(e)))
        return queryset

    def _apply_order(
        self, queryset: QuerySet, order_fields: tuple[str, ...]
    ) -> QuerySet:
        return queryset.order_by(*order_fields)

    def _filter_ts_rows(self, queryset: QuerySet) -> QuerySet:
        if self.latest_ts:
            return queryset.filter(id__in=self._latest_hub_value_date_ids())
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

    def _latest_hub_value_date_ids(self) -> QuerySet:
        """Ids of the rows that are their hub's latest one.

        The latest row of a hub is its newest dated row, or its undated row if
        it has no dated one. Ranked once over the whole table with a window
        function instead of looked up per row by a correlated subquery, which
        Postgres evaluates for every row of every hub before any other filter
        applies - with a long time series that dominates the whole query.

        Built from the bare model so none of the annotation subqueries are
        dragged into this inner query. ``RANK`` rather than ``ROW_NUMBER``
        keeps all tied rows, as a comparison of the value dates would; the
        null ordering is emulated by Django on databases without NULLS LAST.
        """
        ranked = self.hub_value_date.objects.all()
        if self.hub_scope_pk is not None:
            ranked = ranked.filter(hub_id=self.hub_scope_pk)
        ranked = ranked.annotate(
            _latest_rank=Window(
                expression=Rank(),
                partition_by=F("hub_id"),
                order_by=F("value_date_list__value_date").desc(nulls_last=True),
            )
        )
        return ranked.filter(_latest_rank=1).values("id")

    def _filter_session_data(self, queryset: QuerySet) -> QuerySet:
        if not self.annotator.get_ts_satellite_classes():
            return queryset
        end_date = self.session_end_date
        start_date = self.session_start_date
        return queryset.filter(
            (Q(value_date__lte=end_date) & Q(value_date__gte=start_date))
            | Q(value_date__isnull=True)
        )
