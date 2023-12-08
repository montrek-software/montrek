from typing import Any, List, Dict, Type, Tuple
from baseclasses.models import MontrekSatelliteABC
from baseclasses.models import MontrekHubABC
from baseclasses.repositories.annotation_manager import (
    AnnotationsManager,
    SatelliteAnnotationsManager,
    LinkAnnotationsManager,
)
from baseclasses.repositories.subquery_builder import (
    SatelliteSubqueryBuilder,
    LastTSSatelliteSubqueryBuilder,
)
from django.db.models import Q, Subquery, OuterRef, QuerySet
from django.utils import timezone
from django.core.paginator import Paginator
from functools import wraps


class MontrekRepository:
    hub_class = MontrekHubABC

    def __init__(self, request):
        self._annotations = {}
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
        return timezone.datetime.now()

    def std_queryset(self, **kwargs):
        raise NotImplementedError("MontrekRepository has no std_queryset method!")

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

    def add_linked_satellites_field_annotations(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        link_lookup_string: str,
        fields: List[str],
        reference_date: timezone,
    ):
        subquery_builder = SatelliteSubqueryBuilder(
            satellite_class, link_lookup_string, reference_date
        )
        annotations_manager = LinkAnnotationsManager(subquery_builder, satellite_class.__name__)
        self._add_to_annotations(fields, annotations_manager)

    def build_queryset(self) -> QuerySet:
        return self.hub_class.objects.annotate(**self.annotations)

    def rename_field(self, field: str, new_name: str):
        self.annotations[new_name] = self.annotations[field]

    def _add_to_annotations(self, fields: List[str], annotations_manager:AnnotationsManager):
        annotations_manager.query_to_annotations(fields)
        self.annotations.update(annotations_manager.annotations)





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
