from typing import Any, List, Dict, Type, Tuple
from baseclasses.models import MontrekSatelliteABC
from baseclasses.models import MontrekHubABC
from django.db.models import Q, Subquery, OuterRef, QuerySet
from django.utils import timezone


class MontrekRepository:
    hub_class = MontrekHubABC
    def __init__(self, request):
        self._annotations = {}
        self.request = request

    @property
    def annotations(self):
        return self._annotations

    @property
    def session_end_date(self):
        return self.request.session.get("end_date", timezone.now())

    def std_queryset(self, **kwargs):
        raise NotImplementedError("MontrekRepository has no std_queryset method!")

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

    #def _get_date_range_dates(self) -> Tuple[str, str]:
    #    today = timezone.now().date()
    #    default_start_date = today - timedelta(days=30)
    #    default_end_date = today
    #    default_start_date = default_start_date.strftime("%Y-%m-%d")
    #    default_end_date = default_end_date.strftime("%Y-%m-%d")

    #    try:
    #        start_date_str = request.session.get("start_date", default_start_date)
    #    except ValueError:
    #        start_date_str = default_start_date

    #    try:
    #        end_date_str = request.session.get("end_date", default_end_date)
    #    except ValueError:
    #        end_date_str = default_end_date

    #    return start_date_str, end_date_str
