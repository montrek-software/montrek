from django.conf import settings
from typing import Type

from django.db.models.functions import Cast
from django.db.models import Q
from baseclasses.models import (
    MontrekHubABC,
    MontrekManyToManyLinkABC,
    MontrekOneToManyLinkABC,
    MontrekSatelliteABC,
    ValueDateList,
)
from baseclasses.models import MontrekLinkABC
from baseclasses.models import LinkTypeEnum
from django.db.models import CharField, QuerySet, Subquery, OuterRef, Func
from django.utils import timezone


class SubqueryBuilder:
    def build(self, reference_date: timezone.datetime) -> Subquery:
        raise NotImplementedError("SubqueryBuilder has no get_subquery method!")


class SatelliteSubqueryBuilderABC(SubqueryBuilder):
    lookup_field: str = ""

    def __init__(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        field: str,
    ):
        self.satellite_class = satellite_class
        self.field = field
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

    def satellite_subquery(
        self, reference_date: timezone.datetime, lookup_field: str = "pk"
    ) -> Subquery:
        return Subquery(
            self.satellite_class.objects.filter(
                **self.subquery_filter(reference_date, lookup_field=lookup_field)
            ).values(self.field)
        )


class SatelliteSubqueryBuilder(SatelliteSubqueryBuilderABC):
    def build(self, reference_date: timezone.datetime) -> Subquery:
        return Subquery(
            self.get_hub_query(reference_date)
            .annotate(
                **{
                    self.field: self.satellite_subquery(
                        reference_date, lookup_field="hub_entity"
                    ),
                }
            )
            .values(self.field)
        )


class TSSatelliteSubqueryBuilder(SatelliteSubqueryBuilderABC):
    def build(self, reference_date: timezone.datetime) -> Subquery:
        return self.satellite_subquery(reference_date, lookup_field="hub_value_date")


class ValueDateSubqueryBuilder(SubqueryBuilder):
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


class CreatedAtSubqueryBuilder(HubDirectFieldSubqueryBuilder):
    field = "created_at"


class CreatedBySubqueryBuilder(HubDirectFieldSubqueryBuilder):
    field = "created_by"


class LinkedSatelliteSubqueryBuilderBase(SatelliteSubqueryBuilderABC):
    def __init__(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        field: str,
        link_class: Type[MontrekLinkABC],
        last_ts_value: bool,
    ):
        super().__init__(satellite_class, field)

        if link_class.link_type == LinkTypeEnum.NONE:
            raise TypeError(f"{link_class.__name__} must inherit from valid LinkClass!")
        self.link_class = link_class
        self.link_db_name = link_class.__name__.lower()
        self._last_ts_value = last_ts_value

    def get_link_query(
        self, hub_field: str, reference_date: timezone.datetime
    ) -> QuerySet:
        return self.link_class.objects.filter(
            Q(
                **self.subquery_filter(
                    reference_date, lookup_field=hub_field, outer_ref="hub"
                )
            )
            & Q(
                **{
                    f"{hub_field}__state_date_start__lte": reference_date,
                    f"{hub_field}__state_date_end__gt": reference_date,
                }
            ),
        )

    def _link_hubs_and_get_subquery(
        self, hub_field_to: str, hub_field_from: str, reference_date: timezone.datetime
    ) -> Subquery:
        sat_query = self.satellite_class.objects.filter(
            **self.subquery_filter(
                reference_date,
                lookup_field="hub_entity",
                outer_ref=f"{hub_field_to}",
            )
        ).values(self.field)
        query = (
            self.get_link_query(hub_field_from, reference_date)
            .annotate(**{self.field: Subquery(sat_query)})
            .values(self.field)
        )
        query = self._annotate_agg_field(hub_field_to, query)
        return Subquery(query)

    def _link_hubs_and_get_ts_subquery(
        self, hub_field_to: str, hub_field_from: str, reference_date: timezone.datetime
    ) -> Subquery:
        query = (
            self.get_link_query(hub_field_from, reference_date)
            .annotate(
                **{
                    self.field: Subquery(
                        self._annotate_agg_field(
                            hub_field_to,
                            self.satellite_class.objects.filter(
                                Q(
                                    **self.subquery_filter(
                                        reference_date,
                                        lookup_field="hub_value_date",
                                        outer_ref=f"{hub_field_to}__hub_value_date",
                                    )
                                )
                                & Q(
                                    hub_value_date__value_date_list=OuterRef(
                                        f"{hub_field_to}__hub_value_date__value_date_list"
                                    )
                                )
                            ).values(self.field),
                        )
                    )
                }
            )
            .values(self.field)[:1]
        )
        return Subquery(query)

    def _annotate_agg_field(self, hub_field_to: str, query: QuerySet) -> QuerySet:
        if self._is_multiple_allowed(hub_field_to):
            func = get_string_concat_function()
            field_type = CharField
            return query.annotate(
                **{
                    self.field
                    + "agg": Cast(
                        func(Cast(self.field, field_type())),
                        field_type(),
                    )
                }
            ).values(self.field + "agg")
        return query

    def _is_multiple_allowed(self, hub_field_to: str) -> bool:
        _is_many_to_many = isinstance(self.link_class(), MontrekManyToManyLinkABC)
        _is_many_to_one = (
            isinstance(self.link_class(), MontrekOneToManyLinkABC)
            and hub_field_to == "hub_in"
        )
        return _is_many_to_many or _is_many_to_one


class LinkedSatelliteSubqueryBuilder(LinkedSatelliteSubqueryBuilderBase):
    def __init__(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        field: str,
        link_class: Type[MontrekLinkABC],
        last_ts_value: bool,
    ):
        super().__init__(satellite_class, field, link_class, last_ts_value)

    def build(self, reference_date: timezone.datetime) -> Subquery:
        if self.satellite_class.is_timeseries:
            return super()._link_hubs_and_get_ts_subquery(
                "hub_out", "hub_in", reference_date
            )
        else:
            return super()._link_hubs_and_get_subquery(
                "hub_out", "hub_in", reference_date
            )


class ReverseLinkedSatelliteSubqueryBuilder(LinkedSatelliteSubqueryBuilderBase):
    def __init__(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        field: str,
        link_class: Type[MontrekLinkABC],
        last_ts_value: bool,
    ):
        super().__init__(satellite_class, field, link_class, last_ts_value)

    def build(self, reference_date: timezone.datetime) -> Subquery:
        return super()._link_hubs_and_get_subquery("hub_in", "hub_out", reference_date)


class LastTSSatelliteSubqueryBuilder(SatelliteSubqueryBuilderABC):
    def __init__(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        field: str,
        end_date: timezone.datetime,
    ):
        super().__init__(satellite_class, field)
        self.end_date = end_date

    def build(self, reference_date: timezone.datetime) -> Subquery:
        return Subquery(
            self.satellite_class.objects.filter(
                hub_entity=OuterRef(self.lookup_string),
                state_date_start__lte=reference_date,
                state_date_end__gt=reference_date,
                value_date__lte=self.end_date,
            )
            .order_by("-value_date")
            .values(self.field)[:1]
        )


class StringAgg(Func):
    function = "STRING_AGG"
    template = "%(function)s(%(expressions)s, ',')"


class GroupConcat(Func):
    function = "GROUP_CONCAT"
    template = "%(function)s(%(expressions)s SEPARATOR ',')"


def get_string_concat_function():
    engine = settings.DATABASES["default"]["ENGINE"]
    if "mysql" in engine:
        return GroupConcat
    elif "postgresql" in engine:
        return StringAgg
    else:
        raise NotImplementedError(
            f"No function for concatenating list of strings defined for {engine}!"
        )
