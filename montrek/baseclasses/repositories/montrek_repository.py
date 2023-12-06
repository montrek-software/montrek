from typing import Any, List, Dict, Type, Tuple
from baseclasses.models import MontrekSatelliteABC
from baseclasses.models import MontrekHubABC
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

    def std_queryset(self, **kwargs):
        raise NotImplementedError("MontrekRepository has no std_queryset method!")

    def add_satellite_fields_annotations(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        fields: List[str],
        reference_date: timezone,
    ):
        self._query_to_annotations(
            satellite_class, "pk", fields, reference_date, False
        )

    def add_linked_satellites_field_annotations(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        link_lookup_string: str,
        fields: List[str],
        reference_date: timezone,
    ):
        self._query_to_annotations(
            satellite_class, link_lookup_string, fields, reference_date, True
        )

    def _query_to_annotations(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        link_lookup_string: str,
        fields: List[str],
        reference_date: timezone,
        add_class_to_field: bool,
    ):
        for field in fields:
            subquery = self.get_satellite_subquery(
                satellite_class, reference_date, link_lookup_string, field
            )
            if add_class_to_field:
                field = f"{satellite_class.__name__.lower()}.{field}" 
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

    def rename_field(self, field: str, new_name: str):
        self.annotations[new_name] = self.annotations[field]

def paginated_table(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Call the original function
        result = func(*args, **kwargs)

        # Extract request and queryset from result
        request = args[0].request  # Assuming the first argument is 'self' and has 'request'
        queryset = result  # Assuming the original function returns a queryset

        # Pagination logic
        page_number = request.GET.get('page', 1)
        paginate_by = 10  # or you can make this customizable
        paginator = Paginator(queryset, paginate_by)
        page = paginator.get_page(page_number)

        return page
    return wrapper
