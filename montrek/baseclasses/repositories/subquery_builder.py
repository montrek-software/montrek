from enum import Enum
from typing import Any, Callable, Type

from django.db import models
from django.db.models.fields.related import RelatedField

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
from django.db.models import CharField, F, Func, OuterRef, Q, QuerySet, Subquery
from django.db.models.functions import Cast
from django.utils import timezone


class SubqueryBuilder:
    def build(self, reference_date: timezone.datetime) -> Subquery:
        raise NotImplementedError(
            f"{self.__class__.__name__} must be subclassed and the build method must be implemented!"
        )


class SatelliteSubqueryBuilderABC(SubqueryBuilder):
    lookup_field: str = ""

    def __init__(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        field: str,
    ):
        self.satellite_class = satellite_class
        self.field = field
        field_parts = self.field.split("__")
        # TODO: get field of related_model right
        self.field_type = self.satellite_class._meta.get_field(field_parts[0])
        if isinstance(self.field_type, models.ForeignKey):
            self.field_type = models.IntegerField(null=True, blank=True)
        # TODO: remove lookup_string
        self.lookup_string = "pk"

    def get_hub_query(self, reference_date: timezone.datetime) -> QuerySet:
        return self.satellite_class.get_related_hub_class().objects.filter(
            **self.subquery_filter(reference_date, outer_ref="hub")
        )

    def subquery_filter(
        self,
        reference_date: timezone.datetime,
        lookup_field: str = "pk",
        outer_ref: str = "pk",
    ) -> dict[str, object]:
        return {
            lookup_field: OuterRef(outer_ref),
            "state_date_start__lte": reference_date,
            "state_date_end__gt": reference_date,
        }

    def satellite_query(
        self, reference_date: timezone.datetime, lookup_field: str = "pk"
    ) -> QuerySet:
        return self.satellite_class.objects.filter(
            **self.subquery_filter(reference_date, lookup_field=lookup_field)
        ).values(self.field)

    def satellite_subquery(
        self, reference_date: timezone.datetime, lookup_field: str = "pk"
    ) -> Subquery:
        return Subquery(self.satellite_query(reference_date, lookup_field))


class SatelliteSubqueryBuilder(SatelliteSubqueryBuilderABC):
    def build(self, reference_date: timezone.datetime) -> Subquery:
        return Subquery(
            self.get_hub_query(reference_date)
            .annotate(
                **{
                    self.field + "sub": self.satellite_subquery(
                        reference_date, lookup_field="hub_entity"
                    ),
                }
            )
            .values(self.field + "sub")
        )


class TSSatelliteSubqueryBuilder(SatelliteSubqueryBuilderABC):
    def build(self, reference_date: timezone.datetime) -> Subquery:
        return self.satellite_subquery(reference_date, lookup_field="hub_value_date")


class SumTSSatelliteSubqueryBuilder(SatelliteSubqueryBuilder):
    def satellite_query(
        self, reference_date: timezone.datetime, lookup_field: str = "pk"
    ) -> QuerySet:
        sat_query = super().satellite_query(reference_date, "hub_value_date__hub__pk")

        return sat_query.annotate(
            **{
                self.field + "agg": Func(self.field, function="Sum"),
            }
        ).values(self.field + "agg")


class ValueDateSubqueryBuilder(SubqueryBuilder):
    field_type = models.DateField()

    def build(self, reference_date: timezone.datetime) -> Subquery:
        return ValueDateList.objects.filter(pk=OuterRef("value_date_list")).values(
            "value_date"
        )


class HubDirectFieldSubqueryBuilder(SubqueryBuilder):
    field: str = ""

    def __init__(self, hub_class: Type[MontrekHubABC]):
        self.hub_class = hub_class

    def build(self, reference_date: timezone.datetime) -> Subquery:
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
    def __init__(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        field: str,
        link_class: Type[MontrekLinkABC],
        *,
        agg_func: str = "string_concat",
        parent_link_classes: tuple[Type[MontrekLinkABC], ...] = (),
        parent_link_reversed: tuple[bool, ...] | list[bool] = (),
        link_satellite_filter: dict[str, object] = {},
        separator: str = ";",
    ):
        super().__init__(satellite_class, field)

        if link_class.link_type == LinkTypeEnum.NONE:
            raise TypeError(f"{link_class.__name__} must inherit from valid LinkClass!")
        self.link_class = link_class
        self.link_db_name = link_class.__name__.lower()
        self.agg_func = LinkAggFunctionEnum(agg_func)
        self.separator = separator
        if issubclass(link_class, MontrekManyToManyLinkABC) or (
            issubclass(link_class, MontrekOneToManyLinkABC)
            and isinstance(self, ReverseLinkedSatelliteSubqueryBuilder)
        ):
            if agg_func == "string_concat":
                self.field_type = CharField(null=True, blank=True)

        self.parent_link_classes = parent_link_classes
        self.parent_link_reversed = parent_link_reversed
        self.link_satellite_filter = link_satellite_filter

    def get_link_query(
        self, hub_field: str, reference_date: timezone.datetime, outer_ref: str = "hub"
    ) -> QuerySet:
        hub_db_field_name = self._get_parent_db_name(hub_field)
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

    def _get_parent_db_name(self, hub_field: str) -> str:
        db_name = hub_field
        for i, link_class in enumerate(self.parent_link_classes):
            is_reversed = self.parent_link_reversed[i]
            parent_hub_field = "hub_out" if is_reversed else "hub_in"
            db_name += "__" + link_class.__name__.lower() + f"__{parent_hub_field}"
        return db_name

    def _link_hubs_and_get_subquery(
        self,
        hub_field_to: str,
        hub_field_from: str,
        reference_date: timezone.datetime,
    ) -> Subquery:
        sat_query = self.satellite_class.objects.filter(
            **self.link_satellite_filter,
            **self.subquery_filter(
                reference_date,
                lookup_field="hub_entity",
                outer_ref=f"{hub_field_to}",
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
            self.field + "sub": Subquery(
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
                    )
                    .annotate(**{self.field + "sub": F(self.field)})
                    .values(self.field),
                )
            )
        }

    def _annotate_agg_field(self, hub_field_to: str, query: QuerySet) -> QuerySet:
        if self._is_multiple_allowed(hub_field_to):
            if self.agg_func == LinkAggFunctionEnum.SUM:
                return self._annotate_sum(query)
            if self.agg_func == LinkAggFunctionEnum.STRING_CONCAT:
                return self._annotate_string_concat(query, self.separator)
            if self.agg_func == LinkAggFunctionEnum.LATEST:
                return self._annotate_latest(query)
            if self.agg_func == LinkAggFunctionEnum.MEAN:
                return self._annotate_mean(query)
            else:
                raise NotImplementedError(
                    f"Aggregation function {self.agg_func} is not implemented!"
                )
        return query

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
                self.field + "agg": Cast(
                    func(Cast(self.field + "sub", field_type())),
                    field_type(),
                )
            }
        ).values(self.field + "agg")

    def _annotate_latest(self, query: QuerySet) -> QuerySet:
        if self.satellite_class.is_timeseries:
            return query.order_by("-hub_value_date__value_date_list__value_date")[:1]
        else:
            return query.order_by(f"{self.field}sub")[:1]

    def _annotate_mean(self, query: QuerySet) -> QuerySet:
        return query.annotate(
            **{
                self.field + "agg": Func(self.field + "sub", function="Avg"),
            }
        ).values(self.field + "agg")

    def _is_multiple_allowed(self, hub_field_to: str) -> bool:
        _is_many_to_many = isinstance(self.link_class(), MontrekManyToManyLinkABC)
        _is_many_to_one = (
            isinstance(self.link_class(), MontrekOneToManyLinkABC)
            and hub_field_to == "hub_in"
        )
        return _is_many_to_many or _is_many_to_one

    def _get_subquery(
        self, hub_a: str, hub_b: str, reference_date: timezone.datetime
    ) -> Subquery:
        if self.satellite_class.is_timeseries:
            if self.agg_func in [LinkAggFunctionEnum.SUM, LinkAggFunctionEnum.LATEST]:
                return self._link_hubs_and_get_ts_sum_subquery(
                    hub_a, hub_b, reference_date
                )
            return self._link_hubs_and_get_ts_subquery(hub_a, hub_b, reference_date)
        else:
            return self._link_hubs_and_get_subquery(hub_a, hub_b, reference_date)


class LinkedSatelliteSubqueryBuilder(LinkedSatelliteSubqueryBuilderBase):
    def build(self, reference_date: timezone.datetime) -> Subquery:
        return self._get_subquery("hub_out", "hub_in", reference_date)


class ReverseLinkedSatelliteSubqueryBuilder(LinkedSatelliteSubqueryBuilderBase):
    def build(self, reference_date: timezone.datetime) -> Subquery:
        return self._get_subquery("hub_in", "hub_out", reference_date)


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
    elif "postgresql" in engine:
        return lambda *args, **kwargs: StringAgg(*args, separator=separator, **kwargs)
    else:
        raise NotImplementedError(
            f"No function for concatenating list of strings defined for {engine}!"
        )


class LinkAggFunctionEnum(Enum):
    SUM = "sum"
    STRING_CONCAT = "string_concat"
    LATEST = "latest"
    MEAN = "mean"
