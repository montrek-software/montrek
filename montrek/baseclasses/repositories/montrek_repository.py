from typing import Any, List, Dict, Type, Tuple
from dataclasses import dataclass
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

@dataclass
class SatelliteCreationState():
    satellite: MontrekSatelliteABC

class UpdatedSatelliteCreationState(SatelliteCreationState):
    updated_sat: MontrekSatelliteABC
    state: str = "updated"

class NewSatelliteCreationState(SatelliteCreationState):
    state: str = "new"

class ExistingSatelliteCreationState(SatelliteCreationState):
    state: str = "existing"

class MontrekRepository:
    hub_class = MontrekHubABC

    def __init__(self, session_data: Dict[str, Any] = None):
        self._annotations = {}
        self._primary_satellites = []
        self.session_data = session_data
        self._reference_date = None

    @classmethod
    def get_hub_by_id(cls, pk: int) -> MontrekHubABC:
        return cls.hub_class.objects.get(pk=pk)

    @property
    def annotations(self):
        return self._annotations


    @property
    def reference_date(self):
        if self._reference_date is None:
            return timezone.datetime.now()
        return self._reference_date

    @property
    def session_end_date(self):
        return self.session_data.get("end_date", timezone.datetime.max)

    @property
    def session_start_date(self):
        return self.session_data.get("start_date", timezone.datetime.min)

    @reference_date.setter
    def reference_date(self, value):
        self._reference_date = value

    def std_queryset(self, **kwargs):
        raise NotImplementedError("MontrekRepository has no std_queryset method!")

    def std_satellite_fields(self):
        self.std_queryset()
        fields = []
        for satellite_class in self._primary_satellites:
            fields.extend(satellite_class.get_value_fields())
        return fields

    def std_create_object(self, data: Dict[str, Any]):
        query = self.std_queryset()
        hub_entity = self.hub_class()
        selected_satellites = {'new': [], 'existing': [], 'updated': []}
        for satellite_class in self._primary_satellites:
            sat_data = {
                k: v for k, v in data.items() if k in satellite_class.get_value_field_names()
            }
            if len(sat_data) == 0:
                continue
            sat = satellite_class(hub_entity=hub_entity, **sat_data)
            sat = self._process_new_satellite(sat, satellite_class)
            selected_satellites[sat.state].append(sat.satellite)
        self._save_satellites(selected_satellites)
        #TODO: add links

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
        return self.hub_class.objects.annotate(**self.annotations).filter(state_date_start__lte=self.reference_date, state_date_end__gt=self.reference_date)

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

    def _process_new_satellite(
        self,
        satellite: MontrekSatelliteABC,
        satellite_class: Type[MontrekSatelliteABC],
    ) -> SatelliteCreationState:
        # Check if satellite already exists, if it is updating or if it is new
        sat_hash_identifier = satellite.get_hash_identifier
        # TODO: Revisit thsi filter and if it does not work if more Satellite have the same values
        satellite_updates_or_none = (
            satellite_class.objects.filter(hash_identifier=sat_hash_identifier)
            .order_by("-state_date_start")
            .first()
        )
        if satellite_updates_or_none is None:
            return NewSatelliteCreationState(satellite=satellite)
        sat_hash_value = satellite.get_hash_value
        if satellite_updates_or_none.hash_value == sat_hash_value:
            return ExistingSatelliteCreationState(satellite=satellite_updates_or_none)
        return UpdatedSatelliteCreationState(satellite=satellite, updated_sat=satellite_updates_or_none)

    def _save_satellites(self, selected_satellites: Dict[str, List[MontrekSatelliteABC]]):
        creation_date = timezone.datetime.now()
        reference_hub = None
        if len(selected_satellites["new"]) > 0:
            reference_hub = selected_satellites["new"][0].hub_entity
            reference_hub.save()
            for satellite in selected_satellites["new"]:
                satellite.hub_entity = reference_hub
                satellite.save()
        if len(selected_satellites["existing"]) > 0:
            if reference_hub is None:
                # Since there are no new satellites, we store nothing and use the existing sats hub as reference
                reference_hub = selected_satellites["existing"][0].hub_entity
            else:
                # Store copy of existing satellite with new hub
                old_hub = selected_satellites["existing"][0].hub_entity
                old_hub.state_date_end = creation_date
                old_hub.save()
                reference_hub.state_date_start = creation_date
                reference_hub.save()
                for satellite in selected_satellites["existing"]:
                    satellite.state_date_end = creation_date
                    satellite.save()
                    satellite.hub_entity = reference_hub
                    satellite.state_date_start = creation_date
                    satellite.state_date_end = timezone.datetime.max
                    satellite.pk = None
                    satellite.id = None
                    satellite.save()


def paginated_table(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Call the original function
        result = func(*args, **kwargs)

        # Extract request and queryset from result
        session_data = args[0].session_data  # Assuming the first argument is 'self' and has 'request'
        queryset = result  # Assuming the original function returns a queryset

        # Pagination logic
        page_number = session_data.get("page", [1])[0]
        paginate_by = 10  # or you can make this customizable
        paginator = Paginator(queryset, paginate_by)
        page = paginator.get_page(page_number)

        return page

    return wrapper

