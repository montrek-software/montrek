from typing import Any, List, Dict, Type, Tuple
from baseclasses.models import MontrekSatelliteABC
from baseclasses.models import MontrekHubABC
from baseclasses.models import MontrekLinkABC
from baseclasses.repositories.annotation_manager import (
    AnnotationsManager,
    SatelliteAnnotationsManager,
    LinkAnnotationsManager,
)
from baseclasses.repositories.subquery_builder import (
    SatelliteSubqueryBuilder,
    LastTSSatelliteSubqueryBuilder,
    LinkedSatelliteSubqueryBuilder,
    ReverseLinkedSatelliteSubqueryBuilder,
)
from django.db.models import Q, Subquery, OuterRef, QuerySet
from django.utils import timezone
from django.core.paginator import Paginator
from functools import wraps


class MontrekRepository:
    hub_class = MontrekHubABC

    def __init__(self, request):
        self._annotations = {}
        self._primary_satellites = []
        self._reference_date = None
        self.request = request

    @classmethod
    def get_hub_by_id(cls, pk: int) -> MontrekHubABC:
        return cls.hub_class.objects.get(pk=pk)

    @property
    def annotations(self):
        return self._annotations

    @property
    def session_end_date(self):
        return self.request.session.get("end_date", timezone.now())

    @property
    def session_start_date(self):
        return self.request.session.get("start_date", timezone.now())

    @property
    def reference_date(self):
        if self._reference_date is None:
            return timezone.datetime.now()
        return self._reference_date

    @reference_date.setter
    def reference_date(self, value):
        self._reference_date = value

    def std_queryset(self, **kwargs):
        raise NotImplementedError("MontrekRepository has no std_queryset method!")

    def std_create_object(self, data: Dict[str, Any]):
        query = self.std_queryset()
        hub_entity = self.hub_class()
        for satellite_class in self._primary_satellites:
            sat_data = {
                k: v for k, v in data.items() if k in satellite_class.get_value_fields()
            }
            if len(sat_data) == 0:
                continue
            sat = satellite_class(hub_entity=hub_entity, **sat_data)
            sat = self.update_satellite(sat, satellite_class)

    def add_satellite_fields_annotations(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        fields: List[str],
        reference_date: timezone,
    ):
        subquery_builder = SatelliteSubqueryBuilder(
            satellite_class, "pk", reference_date
        )
        annotations_manager = SatelliteAnnotationsManager(subquery_builder)
        self._add_to_annotations(fields, annotations_manager)
        self._add_to_field_container(satellite_class)

    def add_last_ts_satellite_fields_annotations(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        fields: List[str],
        reference_date: timezone,
    ):
        subquery_builder = LastTSSatelliteSubqueryBuilder(
            satellite_class, "pk", reference_date, end_date=self.session_end_date
        )
        annotations_manager = SatelliteAnnotationsManager(subquery_builder)
        self._add_to_annotations(fields, annotations_manager)
        self._add_to_field_container(satellite_class)

    def add_linked_satellites_field_annotations(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        link_class: Type[MontrekLinkABC],
        fields: List[str],
        reference_date: timezone,
        reversed_link: bool = False,
    ):
        if reversed_link:
            subquery_builder = ReverseLinkedSatelliteSubqueryBuilder(
                satellite_class, link_class, reference_date
            )
        else:
            subquery_builder = LinkedSatelliteSubqueryBuilder(
                satellite_class, link_class, reference_date
            )
        annotations_manager = LinkAnnotationsManager(
            subquery_builder, satellite_class.__name__
        )
        self._add_to_annotations(fields, annotations_manager)

    def build_queryset(self) -> QuerySet:
        return self.hub_class.objects.annotate(**self.annotations)

    def rename_field(self, field: str, new_name: str):
        self.annotations[new_name] = self.annotations[field]

    def _add_to_annotations(
        self, fields: List[str], annotations_manager: AnnotationsManager
    ):
        annotations_manager.query_to_annotations(fields)
        self.annotations.update(annotations_manager.annotations)

    def _add_to_field_container(self, satellite_class: Type[MontrekSatelliteABC]):
        if satellite_class not in self._primary_satellites:
            self._primary_satellites.append(satellite_class)

    def update_satellite(
        self,
        satellite: MontrekSatelliteABC,
        satellite_class: Type[MontrekSatelliteABC],
    ) -> MontrekSatelliteABC:
        sat_hash_identifier = satellite.get_hash_identifier
        satellite_updates_or_none = (
            satellite_class.objects.filter(hash_identifier=sat_hash_identifier)
            .order_by("-state_date_start")
            .first()
        )
        if satellite_updates_or_none is None:
            satellite.hub_entity.save()
            satellite.save()
            return satellite
        sat_hash_value = satellite.get_hash_value
        if satellite_updates_or_none.hash_value == sat_hash_value:
            return satellite_updates_or_none
        satellite.hub_entity = satellite_updates_or_none.hub_entity
        state_date = timezone.now()
        new_state_date = state_date
        satellite_updates_or_none.state_date_end = new_state_date
        satellite_updates_or_none.save()
        satellite.state_date_start = state_date
        satellite.save()
        return satellite

def paginated_table(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Call the original function
        result = func(*args, **kwargs)

        # Extract request and queryset from result
        request = args[
            0
        ].request  # Assuming the first argument is 'self' and has 'request'
        queryset = result  # Assuming the original function returns a queryset

        # Pagination logic
        page_number = request.GET.get("page", 1)
        paginate_by = 10  # or you can make this customizable
        paginator = Paginator(queryset, paginate_by)
        page = paginator.get_page(page_number)

        return page

    return wrapper
