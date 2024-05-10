from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from typing import Any, List, Dict, Optional, Type
from baseclasses.models import MontrekSatelliteABC, MontrekTimeSeriesSatelliteABC
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
from baseclasses.dataclasses.montrek_message import MontrekMessageError
from django.db.models import (
    F,
    Q,
    QuerySet,
)
from django.db.models import ManyToManyField
from django.utils import timezone
from django.core.exceptions import FieldError, PermissionDenied


class MontrekRepository:
    hub_class = MontrekHubABC

    def __init__(self, session_data: Dict[str, Any] = {}):
        self._annotations = {}
        self._primary_satellite_classes = []
        self._primary_link_classes = []
        self.session_data = session_data
        self._reference_date = None
        self.messages = []

    @classmethod
    def get_hub_by_id(cls, pk: int) -> MontrekHubABC:
        return cls.hub_class.objects.get(pk=pk)

    @property
    def annotations(self):
        return self._annotations

    @property
    def reference_date(self) -> timezone.datetime:
        if self._reference_date is None:
            return timezone.now()
        return self._reference_date

    @property
    def session_end_date(self) -> timezone.datetime:
        return self._get_session_date("end_date", timezone.datetime.max)

    @property
    def session_start_date(self) -> timezone.datetime:
        return self._get_session_date("start_date", timezone.datetime.min)

    @property
    def session_user_id(self) -> Optional[int]:
        return self.session_data.get("user_id")

    def _get_session_date(
        self, date_type: str, default: timezone.datetime
    ) -> timezone.datetime:
        date_value = self.session_data.get(date_type, default)
        if isinstance(date_value, str):
            date_value = timezone.datetime.strptime(date_value, "%Y-%m-%d")
        return timezone.make_aware(date_value, timezone.get_current_timezone())

    @reference_date.setter
    def reference_date(self, value):
        self._reference_date = value

    @property
    def query_filter(self):
        request_path = self.session_data.get("request_path", "")
        filter = self.session_data.get("filter", {})
        filter = filter.get(request_path, {})
        q_objects = []
        for key, value in filter.items():
            q = Q(**{key: value["filter_value"]})
            q = ~q if value["filter_negate"] else q
            q_objects.append(q)
        return q_objects

    def std_queryset(self, **kwargs):
        raise NotImplementedError("MontrekRepository has no std_queryset method!")

    def object_to_dict(self, obj: MontrekHubABC) -> Dict[str, Any]:
        object_dict = {
            field.name: getattr(obj, field.name)
            for field in self.std_satellite_fields()
        }
        for field in obj._meta.get_fields():
            if isinstance(field, ManyToManyField):
                value = (
                    getattr(obj, field.name)
                    .filter(
                        Q(
                            **{
                                f"{field.name.replace('_','')}__state_date_start__lte": self.reference_date
                            }
                        ),
                        Q(
                            **{
                                f"{field.name.replace('_','')}__state_date_end__gt": self.reference_date
                            }
                        ),
                        Q(state_date_start__lte=self.reference_date),
                        Q(state_date_end__gt=self.reference_date),
                    )
                    .first()
                )
                object_dict[field.name] = value
        object_dict["hub_entity_id"] = obj.pk
        return object_dict

    def std_satellite_fields(self):
        self.std_queryset()
        fields = []
        for satellite_class in self._primary_satellite_classes:
            fields.extend(satellite_class.get_value_fields())
        return fields

    def std_create_object(self, data: Dict[str, Any]) -> MontrekHubABC:
        self._raise_for_anonymous_user()
        self.std_queryset()
        hub_entity = self._get_hub_from_data(data)
        db_creator = DbCreator(self.hub_class, self._primary_satellite_classes)
        created_hub = db_creator.create(data, hub_entity, self.session_user_id)
        db_creator.save_stalled_objects()
        return created_hub

    def create_objects_from_data_frame(
        self, data_frame: pd.DataFrame
    ) -> List[MontrekHubABC]:
        self._raise_for_anonymous_user()
        self.std_queryset()
        db_creator = DbCreator(self.hub_class, self._primary_satellite_classes)
        created_hubs = []
        for _, row in data_frame.iterrows():
            hub_entity = self._get_hub_from_data(row)
            created_hub = db_creator.create(row, hub_entity, self.session_user_id)
            created_hubs.append(created_hub)
        db_creator.save_stalled_objects()
        return created_hubs

    def add_satellite_fields_annotations(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        fields: List[str],
    ):
        subquery_builder = SatelliteSubqueryBuilder(
            satellite_class, "pk", self.reference_date
        )
        annotations_manager = SatelliteAnnotationsManager(subquery_builder)
        self._add_to_annotations(fields, annotations_manager)
        self._add_to_primary_satellite_classes(satellite_class)

    def add_last_ts_satellite_fields_annotations(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        fields: List[str],
    ):
        subquery_builder = LastTSSatelliteSubqueryBuilder(
            satellite_class, "pk", self.reference_date, end_date=self.session_end_date
        )
        annotations_manager = SatelliteAnnotationsManager(subquery_builder)
        self._add_to_annotations(fields, annotations_manager)
        self._add_to_primary_satellite_classes(satellite_class)

    def add_linked_satellites_field_annotations(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        link_class: Type[MontrekLinkABC],
        fields: List[str],
        reversed_link: bool = False,
    ):
        if reversed_link:
            subquery_builder = ReverseLinkedSatelliteSubqueryBuilder(
                satellite_class, link_class, self.reference_date
            )
        else:
            subquery_builder = LinkedSatelliteSubqueryBuilder(
                satellite_class, link_class, self.reference_date
            )
        annotations_manager = LinkAnnotationsManager(
            subquery_builder, satellite_class.__name__
        )
        self._add_to_annotations(fields, annotations_manager)
        self._add_to_primary_link_classes(link_class)

    def build_queryset(self, **filter_kwargs) -> QuerySet:
        queryset = self.hub_class.objects.annotate(**self.annotations).filter(
            Q(state_date_start__lte=self.reference_date),
            Q(state_date_end__gt=self.reference_date),
        )
        try:
            queryset = queryset.filter(*self.query_filter)
        except (FieldError, ValueError) as e:
            self.messages.append(MontrekMessageError(str(e)))
        return queryset

    def build_time_series_queryset(
        self,
        time_series_satellite_class: type[MontrekSatelliteABC],
        reference_date: timezone.datetime,
    ):
        if not issubclass(time_series_satellite_class, MontrekTimeSeriesSatelliteABC):
            raise ValueError(
                f"{time_series_satellite_class.__name__} is not a subclass of MontrekTimeSeriesSatelliteABC"
            )
        return time_series_satellite_class.objects.filter(
            state_date_start__lte=reference_date,
            state_date_end__gte=reference_date,
            value_date__lte=self.session_end_date,
            value_date__gte=self.session_start_date,
        ).order_by("value_date")

    def get_history_queryset(self, pk: int, **kwargs) -> dict[str, QuerySet]:
        self.std_queryset()
        hub = self.hub_class.objects.get(pk=pk)
        satellite_querys = {}
        for sat in self._primary_satellite_classes:
            sat_query = sat.objects.filter(hub_entity=hub).order_by("-created_at")
            sat_query = sat_query.annotate(
                changed_by=F("created_by__email"),
            )
            satellite_querys[sat.__name__] = sat_query
        for link in self._primary_link_classes:
            link_query = link.objects.filter(hub_in=hub).order_by("-created_at")
            satellite_querys[link.__name__] = link_query
        return satellite_querys

    def rename_field(self, field: str, new_name: str):
        self.annotations[new_name] = self.annotations[field]

    def std_delete_object(self, obj: MontrekHubABC):
        obj.state_date_end = timezone.now()
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

    def _get_hub_from_data(self, data: Dict[str, Any]) -> MontrekHubABC:
        if (
            "hub_entity_id" in data
            and data["hub_entity_id"]
            and data["hub_entity_id"] != ""
        ):
            hub_entity = self.hub_class.objects.get(pk=data["hub_entity_id"])
        else:
            hub_entity = self.hub_class(created_by_id=self.session_user_id)
        return hub_entity

    def _raise_for_anonymous_user(self):
        if not self.session_user_id:
            raise PermissionDenied("User not authenticated!")
