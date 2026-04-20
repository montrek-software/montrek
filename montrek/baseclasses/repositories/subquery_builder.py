from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from collections.abc import Callable

from django.db.models.expressions import BaseExpression

from baseclasses.models import (
    LinkTypeEnum,
    MontrekHubABC,
    MontrekLinkABC,
    MontrekManyToManyLinkABC,
    MontrekOneToManyLinkABC,
    MontrekSatelliteABC,
    ValueDateList,
)
from django.conf import settings
from django.db import models
from django.db.models import (
    BooleanField,
    Case,
    CharField,
    F,
    ExpressionWrapper,
    Func,
    IntegerField,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Cast
from django.utils import timezone


@dataclass
class CrossSatelliteFilter:
    """Filter based on a satellite belonging to a different hub, reached from
    the linked hub via a second link.

    Example (HubA perspective, fetching SatB from HubB):
        HubA --LinkHubAHubB--> HubB --SatB (fetch field_b1)
                                   \\
                                    --LinkHubBHubC--> HubC --SatC (filter: field_c = "X")

    satellite_class: the satellite on the cross-hub to filter on (e.g. SatC)
    link_class:      the link connecting the fetched hub to the cross-hub (e.g. LinkHubBHubC)
    filter_dict:     ORM filter kwargs applied to the cross satellite (e.g. {"field_c": "X"})
    reversed_link:   True if the fetched hub sits on the hub_out side of link_class
                     (i.e. the cross hub is reached via hub_in)
    """

    satellite_class: type
    link_class: type
    filter_dict: dict[str, Any] = field(default_factory=dict)
    reversed_link: bool = False


class SubqueryBuilder:
    def build(self, reference_date: timezone.datetime) -> BaseExpression:
        raise NotImplementedError(
            f"{self.__class__.__name__} must be subclassed and the build method must be implemented!"
        )

    def build_subquery(
        self,
        alias_name: str,
        field: str,
    ) -> Subquery | ExpressionWrapper:
        """
        Build a reusable subquery or expression that can be referenced from an
        outer queryset by alias.

        This method complements :meth:`build`. While ``build`` typically
        constructs the primary subquery for a given ``reference_date`` (for
        example, to be used directly in annotations or filters), ``build_subquery``
        is intended to construct a subquery or expression that depends on an
        alias defined in the outer query (for example, an annotated primary key
        or foreign key).

        Args:
            alias_name: The name of the field or annotation on the outer query
                that will be used via ``OuterRef`` inside the subquery.
            field: The name of the field on the target model whose value should
                be returned by the subquery or expression.

        Returns:
            A Django ``Subquery`` or ``ExpressionWrapper`` suitable for use in
            queryset annotations or filters.
        """
        ...


class SatelliteSubqueryBuilderABC(SubqueryBuilder):
    lookup_field: str = ""
    outer_ref: str = ""

    def __init__(
        self,
        satellite_class: type[MontrekSatelliteABC],
    ):
        self.satellite_class = satellite_class

    def subquery_filter(
        self,
        reference_date: timezone.datetime,
        lookup_field: str | None = None,
        outer_ref: str | None = None,
    ) -> dict[str, object]:
        lookup_field = self.lookup_field if lookup_field is None else lookup_field
        outer_ref = self.outer_ref if outer_ref is None else outer_ref
        return {
            lookup_field: OuterRef(outer_ref),
            "state_date_start__lte": reference_date,
            "state_date_end__gt": reference_date,
        }

    def satellite_query(self, reference_date: timezone.datetime) -> QuerySet:
        return self.satellite_class.objects.filter(
            **self.subquery_filter(reference_date)
        ).values("pk")

    def satellite_subquery(self, reference_date: timezone.datetime) -> Subquery:
        return Subquery(self.satellite_query(reference_date))

    def build_alias(self, reference_date: timezone.datetime) -> Subquery:
        return self.satellite_subquery(reference_date)

    def build_subquery(
        self,
        alias_name: str,
        field: str,
    ) -> Subquery:
        sat_query = self.satellite_class.objects.filter(pk=OuterRef(alias_name))
        return Subquery(sat_query.values(field))


class SatelliteSubqueryBuilder(SatelliteSubqueryBuilderABC):
    lookup_field: str = "hub_entity"
    outer_ref: str = "hub_id"


class TSSatelliteSubqueryBuilder(SatelliteSubqueryBuilderABC):
    lookup_field: str = "hub_value_date"
    outer_ref: str = "pk"


class TSSumFieldSubqueryBuilder(SubqueryBuilder):
    def __init__(self, satellite_class, field: str):
        self.satellite_class = satellite_class
        self.field = field

    def build(self, reference_date):
        qs = (
            self.satellite_class.objects.filter(
                hub_value_date__hub_id=OuterRef("hub_id"),
                state_date_start__lte=reference_date,
                state_date_end__gt=reference_date,
            )
            .values("hub_value_date__hub_id")
            .annotate(total=Sum(self.field))
            .values("total")
        )
        return Subquery(qs)


class ValueDateSubqueryBuilder(SubqueryBuilder):
    field_type = models.DateField()

    def build(self, reference_date: timezone.datetime) -> Subquery:
        return ValueDateList.objects.filter(pk=OuterRef("value_date_list")).values(
            "value_date"
        )


class HubDirectFieldSubqueryBuilder(SubqueryBuilder):
    field: str = ""

    def __init__(self, hub_class: type[MontrekHubABC]):
        self.hub_class = hub_class

    def build(self, reference_date: timezone.datetime) -> Subquery:
        # TODO: Rearrange this with an alias
        return Subquery(
            self.hub_class.objects.filter(pk=OuterRef("hub")).values(self.field)
        )


class HubEntityIdSubqueryBuilder(HubDirectFieldSubqueryBuilder):
    field = "id"
    field_type = models.IntegerField()


class CreatedAtSubqueryBuilder(HubDirectFieldSubqueryBuilder):
    field = "created_at"
    field_type = models.DateTimeField()


class CreatedBySubqueryBuilder(HubDirectFieldSubqueryBuilder):
    field = "created_by__email"
    field_type = models.EmailField()


class CommentSubqueryBuilder(HubDirectFieldSubqueryBuilder):
    field = "comment"
    field_type = models.CharField()


class LinkedSatelliteSubqueryBuilderBase(SatelliteSubqueryBuilderABC):
    # Subclasses declare which hub side is the *destination* (satellite owner)
    # and which side anchors the outer-query reference.  Used by the alias
    # optimisation to determine the correct hub fields without re-instantiating
    # a builder just for an isinstance check.
    _hub_field_to: str = ""
    _hub_field_from: str = ""

    def __init__(
        self,
        satellite_class: type[MontrekSatelliteABC],
        field: str,
        link_class: type[MontrekLinkABC],
        *,
        agg_func: str = "string_concat",
        parent_link_classes: tuple[type[MontrekLinkABC], ...] = (),
        parent_link_reversed: tuple[bool, ...] | list[bool] = (),
        link_satellite_filter: dict[str, object] | None = None,
        cross_satellite_filters: tuple[CrossSatelliteFilter, ...] = (),
        separator: str = ";",
    ):
        super().__init__(satellite_class)
        self.field = field
        link_satellite_filter = (
            {} if link_satellite_filter is None else link_satellite_filter
        )

        if link_class.link_type == LinkTypeEnum.NONE:
            raise TypeError(f"{link_class.__name__} must inherit from valid LinkClass!")
        self.link_class = link_class
        self.link_db_name = link_class.__name__.lower()
        self.agg_func = LinkAggFunctionEnum(agg_func)
        self.separator = separator

        self.parent_link_classes = parent_link_classes
        self.parent_link_reversed = parent_link_reversed
        self.link_satellite_filter = link_satellite_filter
        self.cross_satellite_filters = cross_satellite_filters

    def get_link_query(
        self, hub_field: str, reference_date: timezone.datetime, outer_ref: str = "hub"
    ) -> QuerySet:
        hub_db_field_name, parent_link_strings = (
            self._get_parent_db_name_und_link_string(hub_field)
        )
        parent_link_filters = self._get_parent_link_filters(
            reference_date, parent_link_strings
        )
        return self.link_class.objects.filter(
            Q(
                **self.subquery_filter(
                    reference_date,
                    lookup_field=hub_db_field_name,
                    outer_ref=outer_ref,
                )
            )
            & Q(
                **{
                    f"{hub_db_field_name}__state_date_start__lte": reference_date,
                    f"{hub_db_field_name}__state_date_end__gt": reference_date,
                }
            )
            & Q(**parent_link_filters)
        )

    def get_link_hub_value_date_query(
        self, hub_field: str, reference_date: timezone.datetime
    ) -> QuerySet:
        hub_value_date_class = self.satellite_class.hub_value_date.field.related_model

        return hub_value_date_class.objects.filter(
            Q(**{f"hub__{self.link_db_name}__state_date_end__gt": reference_date})
            & Q(**{f"hub__{self.link_db_name}__state_date_start__lte": reference_date})
            & Q(value_date_list=OuterRef("value_date_list"))
            & Q(**{f"hub__{self.link_db_name}__{hub_field}": OuterRef("hub")})
            & Q(
                **{
                    "hub__state_date_start__lte": reference_date,
                    "hub__state_date_end__gt": reference_date,
                }
            ),
        )

    def _get_parent_db_name_und_link_string(
        self, hub_field: str
    ) -> tuple[str, list[str]]:
        db_name = hub_field
        parent_link_strings = []
        for i, link_class in enumerate(self.parent_link_classes):
            is_reversed = self.parent_link_reversed[i]
            parent_hub_field = "hub_out" if is_reversed else "hub_in"
            db_name += "__" + link_class.__name__.lower()
            parent_link_strings.append(db_name)
            db_name += f"__{parent_hub_field}"
        return db_name, parent_link_strings

    def _get_parent_link_filters(
        self, reference_date: timezone.datetime, parent_link_strings: list[str]
    ) -> dict[str, timezone.datetime]:
        parent_link_filters = {}
        for parent_link_string in parent_link_strings:
            parent_link_filters[parent_link_string + "__state_date_end__gt"] = (
                reference_date
            )
            parent_link_filters[parent_link_string + "__state_date_start__lte"] = (
                reference_date
            )
        return parent_link_filters

    def _build_cross_satellite_filter_dict(
        self, reference_date: timezone.datetime
    ) -> dict:
        """Build ORM filter kwargs that traverse from the fetched satellite's hub
        through a second link to a different hub's satellite."""
        result = {}
        hub_prefix = (
            "hub_value_date__hub"
            if self.satellite_class.is_timeseries
            else "hub_entity"
        )

        for csf in self.cross_satellite_filters:
            link_lower = csf.link_class.__name__.lower()
            hub_field = "hub_in" if csf.reversed_link else "hub_out"
            sat_lower = csf.satellite_class.__name__.lower()

            link_path = f"{hub_prefix}__{link_lower}"
            hub_path = f"{link_path}__{hub_field}"
            if getattr(csf.satellite_class, "is_timeseries", False):
                # TS satellites are not directly reachable from the cross-hub;
                # HubForeignKey sets related_name="hub_value_date" on all hub-value-date
                # models, so the path is hub → hub_value_date → satellite.
                sat_path = f"{hub_path}__hub_value_date__{sat_lower}"
            else:
                sat_path = f"{hub_path}__{sat_lower}"

            # Link validity
            result[f"{link_path}__state_date_start__lte"] = reference_date
            result[f"{link_path}__state_date_end__gt"] = reference_date
            # Target hub validity
            result[f"{hub_path}__state_date_start__lte"] = reference_date
            result[f"{hub_path}__state_date_end__gt"] = reference_date
            # Cross satellite validity
            result[f"{sat_path}__state_date_start__lte"] = reference_date
            result[f"{sat_path}__state_date_end__gt"] = reference_date
            # User-supplied field filters
            for key, value in csf.filter_dict.items():
                result[f"{sat_path}__{key}"] = value

        return result

    def _link_hubs_and_get_subquery(
        self,
        hub_field_to: str,
        hub_field_from: str,
        reference_date: timezone.datetime,
    ) -> Subquery:
        sat_query = self.satellite_class.objects.filter(
            **self.link_satellite_filter,
            **self._build_cross_satellite_filter_dict(reference_date),
            **self.subquery_filter(
                reference_date,
                lookup_field="hub_entity",
                outer_ref=hub_field_to,
            ),
        ).values(self.field)
        query = (
            self.get_link_query(hub_field_from, reference_date)
            .annotate(**{self.field + "sub": Subquery(sat_query)})
            .values(self.field + "sub")
        )
        query = self._annotate_agg_field(hub_field_to, query)
        return Subquery(query)

    def _link_hubs_and_get_ts_subquery(
        self, hub_field_to: str, hub_field_from: str, reference_date: timezone.datetime
    ) -> Subquery:
        query = (
            self.get_link_hub_value_date_query(hub_field_from, reference_date)
            .annotate(
                **self._annotate_ts_satellite_dict(
                    hub_field_to, reference_date, "pk", "hub_value_date"
                )
            )
            .values(self.field + "sub")
        )
        query = self._annotate_agg_field(hub_field_to, query)
        return Subquery(query)

    def _link_hubs_and_get_ts_sum_subquery(
        self, hub_field_to: str, hub_field_from: str, reference_date: timezone.datetime
    ) -> Subquery:
        query = self.get_link_query(hub_field_from, reference_date)
        query = query.annotate(
            **self._annotate_ts_satellite_dict(
                hub_field_to, reference_date, hub_field_to, "hub_value_date__hub"
            )
        ).values(self.field + "sub")
        query = self._annotate_sum(query)
        return Subquery(query)

    def _annotate_ts_satellite_dict(
        self,
        hub_field_to: str,
        reference_date: timezone.datetime,
        outer_ref_field: str,
        lookup_field: str,
    ) -> dict:
        return {
            self.field
            + "sub": Subquery(
                self._annotate_agg_field(
                    hub_field_to,
                    self.satellite_class.objects.filter(
                        Q(
                            **self.subquery_filter(
                                reference_date,
                                lookup_field=lookup_field,
                                outer_ref=outer_ref_field,
                            )
                        ),
                        Q(**self.link_satellite_filter),
                        Q(**self._build_cross_satellite_filter_dict(reference_date)),
                    )
                    .annotate(**{self.field + "sub": F(self.field)})
                    .values(self.field),
                )
            )
        }

    def _annotate_agg_field(self, hub_field_to: str, query: QuerySet) -> QuerySet:
        if not self._is_multiple_allowed(hub_field_to):
            return query
        annotators = {
            LinkAggFunctionEnum.SUM: lambda q: self._annotate_sum(q),
            LinkAggFunctionEnum.SUM_VALUE_DATE: lambda q: self._annotate_sum(q),
            LinkAggFunctionEnum.STRING_CONCAT: lambda q: self._annotate_string_concat(
                q, self.separator
            ),
            LinkAggFunctionEnum.LATEST: lambda q: self._annotate_latest(q),
            LinkAggFunctionEnum.MEAN: lambda q: self._annotate_mean(q),
            LinkAggFunctionEnum.COUNT: lambda q: self._annotate_count(q),
            LinkAggFunctionEnum.ALL: lambda q: self._annotate_all(q),
        }
        if self.agg_func not in annotators:
            raise NotImplementedError(
                f"Aggregation function {self.agg_func} is not implemented!"
            )
        return annotators[self.agg_func](query)

    def _annotate_sum(self, query: QuerySet) -> QuerySet:
        return query.annotate(
            **{
                self.field + "agg": Func(self.field + "sub", function="Sum"),
            }
        ).values(self.field + "agg")

    def _annotate_string_concat(self, query: QuerySet, separator: str) -> QuerySet:
        func = get_string_concat_function(separator)
        field_type = CharField
        return query.annotate(
            **{
                self.field
                + "agg": Cast(
                    func(Cast(self.field + "sub", field_type())),
                    field_type(),
                )
            }
        ).values(self.field + "agg")

    def _annotate_latest(self, query: QuerySet) -> QuerySet:
        if self.satellite_class.is_timeseries:
            return query.order_by("-hub_value_date__value_date_list__value_date")[:1]
        return query.order_by(f"{self.field}sub")[:1]

    def _annotate_mean(self, query: QuerySet) -> QuerySet:
        return query.annotate(
            **{
                self.field + "agg": Func(self.field + "sub", function="Avg"),
            }
        ).values(self.field + "agg")

    def _annotate_count(self, query: QuerySet) -> QuerySet:
        return query.annotate(
            **{
                self.field + "agg": Func(self.field + "sub", function="Count"),
            }
        ).values(self.field + "agg")

    def _annotate_all(self, query: QuerySet) -> QuerySet:
        # Map each value to 1 (truthy) or 0 (falsy), then take MIN across all rows.
        # MIN = 1 iff every value was truthy → True; any falsy value → MIN = 0 → False.
        # Only explicit False/0 is treated as falsy. NULL (no matching satellite, e.g.
        # excluded by a CrossSatelliteFilter) is skipped, consistent with how SQL
        # aggregates handle NULL (they ignore NULL values).
        # A separate Q is used instead of __in=[False, 0] to avoid type-coercion errors
        # when the field is e.g. IntegerField (which rejects "").
        falsy_condition = Q(**{f"{self.field}sub": False})
        min_field = f"{self.field}_all_min"
        return (
            query.annotate(
                **{
                    min_field: Func(
                        Case(
                            When(
                                **{f"{self.field}sub__isnull": True},
                                then=Value(None, output_field=IntegerField()),
                            ),
                            When(falsy_condition, then=Value(0)),
                            default=Value(1),
                            output_field=IntegerField(),
                        ),
                        function="Min",
                    )
                }
            )
            .annotate(
                **{
                    self.field
                    + "agg": Case(
                        When(
                            **{f"{min_field}__isnull": True},
                            then=Value(None, output_field=BooleanField()),
                        ),
                        When(**{min_field: 0}, then=Value(False)),
                        default=Value(True),
                        output_field=BooleanField(),
                    )
                }
            )
            .values(self.field + "agg")
        )

    def _is_multiple_allowed(self, hub_field_to: str) -> bool:
        _is_many_to_many = issubclass(self.link_class, MontrekManyToManyLinkABC)
        _is_many_to_many_parent = any(
            issubclass(parent_link_class, MontrekManyToManyLinkABC)
            for parent_link_class in self.parent_link_classes
        )
        _is_many_to_one_parent = False
        for i, parent_link_class in enumerate(self.parent_link_classes):
            parent_reversed = self.parent_link_reversed[i]
            if (
                issubclass(parent_link_class, MontrekOneToManyLinkABC)
                and parent_reversed
            ):
                _is_many_to_many_parent = True
                break

        _is_many_to_one = issubclass(self.link_class, MontrekOneToManyLinkABC) and (
            hub_field_to == "hub_in"
        )
        return (
            _is_many_to_many
            or _is_many_to_one
            or _is_many_to_many_parent
            or _is_many_to_one_parent
        )

    def _build_scalar_alias(
        self,
        hub_field_to: str,
        hub_field_from: str,
        reference_date: timezone.datetime,
    ) -> Subquery:
        """Return a scalar subquery that resolves to the linked satellite's pk.

        Mirrors :meth:`_link_hubs_and_get_subquery` but returns ``pk`` instead
        of a field value so the result can be stored as a queryset alias and
        reused by multiple cheap single-column field projections.

        Only valid for scalar (non-multiple) links.
        """
        sat_pk_qs = self.satellite_class.objects.filter(
            **self.link_satellite_filter,
            **self._build_cross_satellite_filter_dict(reference_date),
            **self.subquery_filter(
                reference_date,
                lookup_field="hub_entity",
                outer_ref=hub_field_to,
            ),
        ).values("pk")[:1]
        return Subquery(
            self.get_link_query(hub_field_from, reference_date)
            .annotate(_lsat_pk=Subquery(sat_pk_qs))
            .values("_lsat_pk")[:1]
        )

    def _get_subquery(
        self, hub_a: str, hub_b: str, reference_date: timezone.datetime
    ) -> Subquery:
        if self.satellite_class.is_timeseries:
            if self.agg_func in [LinkAggFunctionEnum.SUM, LinkAggFunctionEnum.LATEST]:
                return self._link_hubs_and_get_ts_sum_subquery(
                    hub_a, hub_b, reference_date
                )
            return self._link_hubs_and_get_ts_subquery(hub_a, hub_b, reference_date)
        return self._link_hubs_and_get_subquery(hub_a, hub_b, reference_date)


class LinkedSatelliteSubqueryBuilder(LinkedSatelliteSubqueryBuilderBase):
    _hub_field_to: str = "hub_out"
    _hub_field_from: str = "hub_in"

    def build(self, reference_date: timezone.datetime) -> Subquery:
        return self._get_subquery("hub_out", "hub_in", reference_date)

    def build_alias(self, reference_date: timezone.datetime) -> Subquery:
        return self._build_scalar_alias("hub_out", "hub_in", reference_date)


class ReverseLinkedSatelliteSubqueryBuilder(LinkedSatelliteSubqueryBuilderBase):
    _hub_field_to: str = "hub_in"
    _hub_field_from: str = "hub_out"

    def build(self, reference_date: timezone.datetime) -> Subquery:
        return self._get_subquery("hub_in", "hub_out", reference_date)

    def build_alias(self, reference_date: timezone.datetime) -> Subquery:
        return self._build_scalar_alias("hub_in", "hub_out", reference_date)


class StringAgg(Func):
    function = "STRING_AGG"

    def __init__(self, *expressions, separator, **extra):
        self.template = f"{self.function}(%(expressions)s, '{separator}')"
        super().__init__(*expressions, template=self.template, **extra)


class GroupConcat(Func):
    function = "GROUP_CONCAT"

    def __init__(self, *expressions, separator, **extra):
        self.template = f"{self.function}(%(expressions)s SEPARATOR '{separator}')"
        super().__init__(*expressions, template=self.template, **extra)


def get_string_concat_function(separator: str) -> Callable[..., Any]:
    engine = settings.DATABASES["default"]["ENGINE"]
    if "mysql" in engine:
        return lambda *args, **kwargs: GroupConcat(*args, separator=separator, **kwargs)
    if "postgresql" in engine:
        return lambda *args, **kwargs: StringAgg(*args, separator=separator, **kwargs)
    raise NotImplementedError(
        f"No function for concatenating list of strings defined for {engine}!"
    )


class LinkAggFunctionEnum(Enum):
    SUM = "sum"
    SUM_VALUE_DATE = "sum_value_date"
    STRING_CONCAT = "string_concat"
    LATEST = "latest"
    MEAN = "mean"
    COUNT = "count"
    ALL = "all"
