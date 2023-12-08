from typing import Type, List
from baseclasses.models import MontrekSatelliteABC
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
