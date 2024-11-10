from django.conf import settings
from typing import Type

from django.db.models.functions import Cast
from django.db.models import Q
from baseclasses.models import (
    MontrekManyToManyLinkABC,
    MontrekSatelliteABC,
    ValueDateList,
)
from baseclasses.models import MontrekTimeSeriesSatelliteABC
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
        self._last_ts_value = last_ts_value

    def get_linked_hub_query(
        self, hub_field: str, reference_date: timezone.datetime
    ) -> QuerySet:
        return self.link_class.get_related_hub_class(hub_field).objects.filter(
            **self.subquery_filter(reference_date, outer_ref="hub")
        )

    def _link_hubs_and_get_subquery(
        self, hub_field_to: str, hub_field_from: str, reference_date: timezone.datetime
    ) -> Subquery:
        query = (
            self.get_linked_hub_query(hub_field_from, reference_date)
            .annotate(
                **{
                    self.field: Subquery(
                        self.satellite_class.objects.filter(
                            hub_entity=OuterRef(
                                f"{self.link_class.__name__.lower()}__{hub_field_to}"
                            )
                        ).values(self.field)
                    )
                }
            )
            .values(self.field)
        )
        return Subquery(query)

    def _link_hubs_and_get_ts_subquery(
        self, hub_field_to: str, hub_field_from: str, reference_date: timezone.datetime
    ) -> Subquery:
        query = (
            self.get_linked_hub_query(hub_field_from, reference_date)
            .annotate(
                **{
                    self.field: Subquery(
                        self.satellite_class.objects.filter(
                            Q(
                                hub_value_date=OuterRef(
                                    f"{self.link_class.__name__.lower()}__{hub_field_to}__hub_value_date"
                                )
                            )
                            & Q(
                                hub_value_date__value_date_list=OuterRef(
                                    "hub_value_date__value_date_list"
                                )
                            )
                        ).values(self.field)
                    )
                }
            )
            .values(self.field)[:1]
        )
        return Subquery(query)
        hub_out_query = self.link_class.objects.filter(
            state_date_start__lte=reference_date,
            state_date_end__gt=reference_date,
        ).values(hub_field_a)
        link_filter_dict = {
            f"hub_entity__{self.link_class.__name__.lower()}__{hub_field_b}": OuterRef(
                "pk"
            ),
            f"hub_entity__{self.link_class.__name__.lower()}__state_date_start__lte": reference_date,
            f"hub_entity__{self.link_class.__name__.lower()}__state_date_end__gt": reference_date,
        }

        satellite_field_query = self.satellite_class.objects.filter(
            hub_entity__in=Subquery(hub_out_query),
            state_date_start__lte=reference_date,
            state_date_end__gt=reference_date,
            **link_filter_dict,
        ).values(self.field)
        if isinstance(self.link_class(), MontrekManyToManyLinkABC):
            # In case of many-to-may links we return the return values concatenated as characters by default
            func = get_string_concat_function()
            satellite_field_query = satellite_field_query.annotate(
                **{
                    self.field
                    + "agg": Cast(
                        func(Cast(self.field, CharField())),
                        CharField(),
                    )
                }
            ).values(self.field + "agg")
        if isinstance(self.satellite_class(), MontrekTimeSeriesSatelliteABC):
            if self._last_ts_value:
                satellite_field_query = (
                    satellite_field_query.filter(value_date__lte=reference_date)
                    .order_by("-value_date")
                    .values(self.field)[:1]
                )
            else:
                satellite_field_query = satellite_field_query.filter(
                    value_date=OuterRef("value_date")
                ).values(self.field)[:1]

        return Subquery(satellite_field_query)


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
