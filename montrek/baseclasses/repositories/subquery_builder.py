from typing import Type, List
from baseclasses.models import MontrekSatelliteABC
from baseclasses.models import MontrekTimeSeriesSatelliteABC
from baseclasses.models import MontrekLinkABC
from baseclasses.models import LinkTypeEnum
from django.db.models import Subquery, OuterRef
from django.utils import timezone
class SubqueryBuilder:
    def get_subquery(self, field: str) -> Subquery:
        raise NotImplementedError("SubqueryBuilder has no get_subquery method!")


class SatelliteSubqueryBuilder(SubqueryBuilder):
    def __init__(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        lookup_string: str,
        reference_date: timezone,
    ):
        self.satellite_class = satellite_class
        self.lookup_string = lookup_string
        self.reference_date = reference_date
        super().__init__()

    def get_subquery(self, field: str) -> Subquery:
        return Subquery(
            self.satellite_class.objects.filter(
                hub_entity=OuterRef(self.lookup_string),
                state_date_start__lte=self.reference_date,
                state_date_end__gt=self.reference_date,
            ).values(field)
        )


class LastTSSatelliteSubqueryBuilder(SubqueryBuilder):
    def __init__(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        lookup_string: str,
        reference_date: timezone,
        end_date: timezone,
    ):
        self.satellite_class = satellite_class
        self.lookup_string = lookup_string
        self.reference_date = reference_date
        self.end_date = end_date
        super().__init__()

    def get_subquery(self, field: str) -> Subquery:
        return Subquery(
            self.satellite_class.objects.filter(
                hub_entity=OuterRef(self.lookup_string),
                state_date_start__lte=self.reference_date,
                state_date_end__gt=self.reference_date,
                value_date__lte=self.end_date,
            )
            .order_by("-value_date")
            .values(field)[:1]
        )

class LinkedSatelliteSubqueryBuilderBase(SubqueryBuilder):
    def __init__(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        link_class: Type[MontrekLinkABC],
        reference_date: timezone,
    ):
        self.satellite_class = satellite_class
        if link_class.link_type == LinkTypeEnum.NONE:
            raise TypeError(f"{link_class.__name__} must inherit from valid LinkClass!")
        self.link_class = link_class
        self.reference_date = reference_date
        super().__init__()

    def get_subquery(self, field: str, hub_field_a, hub_field_b) -> Subquery:
        hub_out_query = self.link_class.objects.filter(
            state_date_start__lte=self.reference_date,
            state_date_end__gt=self.reference_date,
        ).values(hub_field_a)
        link_filter_dict = {f'hub_entity__{self.link_class.__name__.lower()}__{hub_field_b}':OuterRef("pk"),
               f"hub_entity__{self.link_class.__name__.lower()}__state_date_start__lte":self.reference_date,
               f"hub_entity__{self.link_class.__name__.lower()}__state_date_end__gt":self.reference_date,
              }

        satellite_field_query = self.satellite_class.objects.filter(
            hub_entity__in=Subquery(hub_out_query),
            state_date_start__lte=self.reference_date,
            state_date_end__gt=self.reference_date,
            **link_filter_dict
        ).values(field)
        if isinstance(self.satellite_class(), MontrekTimeSeriesSatelliteABC): 
            satellite_field_query = satellite_field_query.filter(value_date__lte=self.reference_date)
        breakpoint()
        return Subquery(satellite_field_query)

class LinkedSatelliteSubqueryBuilder(LinkedSatelliteSubqueryBuilderBase):
    def __init__(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        link_class: Type[MontrekLinkABC],
        reference_date: timezone,
    ):
        super().__init__(satellite_class, link_class, reference_date)

    def get_subquery(self, field: str) -> Subquery:
        return super().get_subquery(field, "hub_out", "hub_in")

class ReverseLinkedSatelliteSubqueryBuilder(LinkedSatelliteSubqueryBuilderBase):
    def __init__(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        link_class: Type[MontrekLinkABC],
        reference_date: timezone,
    ):
        super().__init__(satellite_class, link_class, reference_date)

    def get_subquery(self, field: str) -> Subquery:
        return super().get_subquery(field, "hub_in", "hub_out")
