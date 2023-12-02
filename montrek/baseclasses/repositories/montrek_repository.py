from typing import Any, List, Dict, Type
from baseclasses.models import MontrekSatelliteABC
from baseclasses.models import MontrekHubABC
from django.db.models import Q, Subquery, OuterRef, QuerySet
from django.utils import timezone


class MontrekRepository:
    def __init__(self, hub_class: Type[MontrekHubABC]):
        self.hub_class = hub_class
        self._annotations = {}

    @property
    def annotations(self):
        return self._annotations

    def detail_queryset(self, **kwargs):
        raise NotImplementedError("MontrekRepository has no detail_queryset method!")

    def table_queryset(self, **kwargs):
        raise NotImplementedError("MontrekRepository has no table_queryset method!")

    def add_satellite_fields_annotations(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        fields: List[str],
        reference_date: timezone,
    ):
        self.add_linked_satellites_field_annotations(
            satellite_class, "pk", fields, reference_date
        )

    def add_linked_satellites_field_annotations(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        link_lookup_string: str,
        fields: List[str],
        reference_date: timezone,
    ) -> Dict[str, Subquery]:
        for field in fields:
            subquery = self.get_satellite_subquery(
                satellite_class, reference_date, link_lookup_string, field
            )
            self._annotations[field] = subquery

    def get_satellite_subquery(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        reference_date: timezone,
        lookup_string: str,
        field: str,
    ) -> Subquery:
        return Subquery(
            satellite_class.objects.filter(
                hub_entity=OuterRef(lookup_string),
                state_date_start__lte=reference_date,
                state_date_end__gt=reference_date,
            ).values(field)
        )

    def build_queryset(self) -> QuerySet:
        return self.hub_class.objects.annotate(**self.annotations)
