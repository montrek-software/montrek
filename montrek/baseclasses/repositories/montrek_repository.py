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
from baseclasses.repositories.db_creator import DbCreator
from django.db.models import Q, Subquery, OuterRef, QuerySet
from django.db.models import ManyToManyField
from django.utils import timezone
from django.core.paginator import Paginator
from functools import wraps


class MontrekRepository:
    hub_class = MontrekHubABC

    def __init__(self, session_data: Dict[str, Any] = None):
        self._annotations = {}
        self._primary_satellite_classes = []
        self._primary_link_classes = []
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

    def object_to_dict(self, obj: MontrekHubABC) -> Dict[str, Any]:
        object_dict = {
            field.name: getattr(obj, field.name)
            for field in self.std_satellite_fields()
        }
        for field in obj._meta.get_fields():
            if isinstance(field, ManyToManyField):
                value = getattr(obj, field.name).filter(
                    Q(**{f"{field.name.replace('_','')}__state_date_start__lte": self.reference_date}),
                    Q(**{f"{field.name.replace('_','')}__state_date_end__gt": self.reference_date}),
                    Q(state_date_start__lte=self.reference_date),
                    Q(state_date_end__gt=self.reference_date),
                ).first()
                object_dict[field.name] = value
        return object_dict

    def std_satellite_fields(self):
        self.std_queryset()
        fields = []
        for satellite_class in self._primary_satellite_classes:
            fields.extend(satellite_class.get_value_fields())
        return fields

    def std_create_object(self, data: Dict[str, Any]):
        self.std_queryset()
        hub_entity = self.hub_class()
        db_creator = DbCreator(
            hub_entity, self._primary_satellite_classes
        )
        db_creator.create(data)

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
        self._add_to_primary_satellite_classes(satellite_class)

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
        self._add_to_primary_satellite_classes(satellite_class)

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
        self._add_to_primary_link_classes(link_class)

    def build_queryset(self) -> QuerySet:
        return self.hub_class.objects.annotate(**self.annotations).filter(
            state_date_start__lte=self.reference_date,
            state_date_end__gt=self.reference_date,
        )

    def rename_field(self, field: str, new_name: str):
        self.annotations[new_name] = self.annotations[field]

    def std_delete_object(self, obj: MontrekHubABC):
        obj.state_date_end = timezone.datetime.now()
        obj.save()

    def _add_to_annotations(
        self, fields: List[str], annotations_manager: AnnotationsManager
    ):
        annotations_manager.query_to_annotations(fields)
        self.annotations.update(annotations_manager.annotations)

    def _add_to_primary_satellite_classes(
        self, satellite_class: Type[MontrekSatelliteABC]
    ):
        if satellite_class not in self._primary_satellite_classes:
            self._primary_satellite_classes.append(satellite_class)

    def _add_to_primary_link_classes(self, link_class: Type[MontrekLinkABC]):
        if link_class not in self._primary_link_classes:
            self._primary_link_classes.append(link_class)

def paginated_table(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Call the original function
        result = func(*args, **kwargs)

        # Extract request and queryset from result
        session_data = args[
            0
        ].session_data  # Assuming the first argument is 'self' and has 'request'
        queryset = result  # Assuming the original function returns a queryset

        # Pagination logic
        page_number = session_data.get("page", [1])[0]
        paginate_by = 10  # or you can make this customizable
        paginator = Paginator(queryset, paginate_by)
        page = paginator.get_page(page_number)

        return page

    return wrapper
