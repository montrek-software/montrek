from copy import deepcopy
from dataclasses import dataclass

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
from baseclasses.dataclasses.montrek_message import (
    MontrekMessageError,
    MontrekMessageWarning,
)
from django.db.models import (
    F,
    Q,
    OuterRef,
    QuerySet,
    Subquery,
)
from django.db.models import ManyToManyField
from django.utils import timezone
from django.core.exceptions import FieldError, PermissionDenied

from baseclasses.repositories.filter_decoder import FilterDecoder


@dataclass
class TSQueryContainer:
    queryset: QuerySet
    fields: List[str]
    satellite_class: type[MontrekTimeSeriesSatelliteABC]


class MontrekRepository:
    hub_class = MontrekHubABC

    def __init__(self, session_data: Dict[str, Any] = {}):
        self._annotations = {}
        self._primary_satellite_classes = []
        self._primary_link_classes = []
        self._ts_queryset_containers = []
        self.session_data = session_data
        self._reference_date = None
        self.messages = []
        self._is_built = False
        self.calculated_fields: list[str] = []
        self.linked_fields: list[str] = []

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
    def query_filter(self) -> Q:
        request_path = self.session_data.get("request_path", "")
        filter = self.session_data.get("filter", {})
        filter = filter.get(request_path, {})
        return FilterDecoder.decode_dict_to_query(filter)

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
        if not self._is_built:
            self.std_queryset()
        fields = []
        for satellite_class in self._primary_satellite_classes:
            fields.extend(satellite_class.get_value_fields())
        return fields

    def _get_satellite_field_names(self, is_time_series: bool) -> list[str]:
        if not self._is_built:
            self.std_queryset()

        fields = []
        for satellite_class in self._primary_satellite_classes:
            if (
                isinstance(satellite_class(), MontrekTimeSeriesSatelliteABC)
                == is_time_series
            ):
                fields.extend(satellite_class.get_value_field_names())

        common_fields = ["hub_entity_id"]
        if is_time_series:
            common_fields.append("value_date")

        return list(set(fields)) + common_fields

    def get_static_satellite_field_names(self) -> list[str]:
        return self._get_satellite_field_names(is_time_series=False)

    def get_time_series_satellite_field_names(self) -> list[str]:
        return self._get_satellite_field_names(is_time_series=True)

    def get_all_fields(self):
        satellite_fields = [field.name for field in self.std_satellite_fields()]
        return satellite_fields + self.calculated_fields + self.linked_fields

    def get_all_annotated_fields(self):
        if not self._is_built:
            self.std_queryset()
        return list(self.annotations.keys())

    def std_create_object(self, data: Dict[str, Any]) -> MontrekHubABC:
        self._raise_for_anonymous_user()
        if not self._is_built:
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
        link_columns = [col for col in data_frame.columns if col.startswith("link_")]
        static_fields = self.get_static_satellite_field_names()
        static_columns = [col for col in static_fields if col in data_frame.columns]
        ts_fields = self.get_time_series_satellite_field_names()
        ts_columns = [col for col in ts_fields if col in data_frame.columns]
        if static_columns:
            if ts_columns:
                # When static data and ts data is combined, the static data will be doubled in multiple lines
                # For cleaning purposes we drop duplicates here
                static_df = data_frame.loc[:, static_columns]
                static_df = static_df.drop_duplicates()
                static_df = static_df.join(data_frame.loc[:, link_columns])
            else:
                static_df = data_frame.loc[:, static_columns + link_columns]
            static_hubs = self._create_objects_from_data_frame(static_df)
        else:
            static_hubs = []
        if ts_columns:
            ts_hubs = self._create_objects_from_data_frame(
                data_frame.loc[:, ts_columns + link_columns]
            )
        else:
            ts_hubs = []
        return list(set(static_hubs + ts_hubs))

    def _create_objects_from_data_frame(
        self, data_frame: pd.DataFrame
    ) -> List[MontrekHubABC]:
        data_frame = self._drop_empty_rows(data_frame)
        data_frame = self._drop_duplicates(data_frame)
        self._raise_for_duplicated_entries(data_frame)
        if not self._is_built:
            self.std_queryset()
        db_creator = DbCreator(self.hub_class, self._primary_satellite_classes)
        created_hubs = []
        for _, row in data_frame.iterrows():
            row = row.to_dict()
            for key, value in row.items():
                if not isinstance(value, (list, dict)) and pd.isna(value):
                    row[key] = None
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
        if satellite_class.is_timeseries:
            ts_container = self.build_time_series_queryset_container(
                satellite_class, fields
            )
            self._ts_queryset_containers.append(ts_container)
        else:
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
        self.linked_fields.extend(fields)

    def build_queryset(self, **filter_kwargs) -> QuerySet:
        base_query = self._get_base_query()
        queryset = base_query.annotate(**self.annotations).filter(
            Q(state_date_start__lte=self.reference_date),
            Q(state_date_end__gt=self.reference_date),
        )
        queryset = self._apply_filter(queryset)
        self._is_built = True
        return queryset

    def build_time_series_queryset_container(
        self,
        time_series_satellite_class: type[MontrekSatelliteABC],
        fields: list[str],
    ) -> TSQueryContainer:
        if not issubclass(time_series_satellite_class, MontrekTimeSeriesSatelliteABC):
            raise ValueError(
                f"{time_series_satellite_class.__name__} is not a subclass of MontrekTimeSeriesSatelliteABC"
            )
        satellite_class_name = time_series_satellite_class.__name__.lower()
        fields = [field for field in fields if field != "value_date"]
        field_map = {field: F(f"{satellite_class_name}__{field}") for field in fields}
        field_map["value_date"] = F(f"{satellite_class_name}__value_date")
        queryset = self.hub_class.objects.filter(
            (
                Q(
                    **{
                        f"{satellite_class_name}__state_date_start__lte": self.reference_date
                    }
                )
                & Q(
                    **{
                        f"{satellite_class_name}__state_date_end__gt": self.reference_date
                    }
                )
            )
            | Q(**{f"{satellite_class_name}__state_date_end": None})
        ).annotate(**field_map)
        queryset = queryset.filter(
            (
                Q(value_date__lte=self.session_end_date)
                & Q(value_date__gte=self.session_start_date)
            )
            | Q(value_date=None)
        )
        return TSQueryContainer(
            queryset=queryset,
            fields=fields,
            satellite_class=time_series_satellite_class,
        )

    def get_history_queryset(self, pk: int, **kwargs) -> dict[str, QuerySet]:
        if not self._is_built:
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

    def _apply_filter(self, queryset: QuerySet) -> QuerySet:
        try:
            queryset = queryset.filter(self.query_filter)
        except (FieldError, ValueError) as e:
            self.messages.append(MontrekMessageError(str(e)))
        return queryset

    def _get_base_query(self) -> QuerySet:
        # Usually every query starts with all hubs of the repositories hub_class.
        # If there is a time_series involved, the query is built from there.
        if len(self._ts_queryset_containers) == 0:
            return self.hub_class.objects.all()
        return self._build_ts_base_query()

    def _build_ts_base_query(self) -> QuerySet:
        # If there are more than one base queries registered, we annotate them in the first step and return everything as base query
        base_query = self._ts_queryset_containers[0].queryset
        base_annotation_dict = {}
        base_container = self._ts_queryset_containers[0]
        for ts_queryset_container in self._ts_queryset_containers[1:]:
            container_query = ts_queryset_container.queryset
            base_query = self._get_extended_container_queryset(
                base_container, container_query
            )
            container_fields = ts_queryset_container.fields

            subquery = container_query.filter(
                value_date=OuterRef("value_date"), pk=OuterRef("pk")
            )
            annotation_dict = {
                field: Subquery(subquery.values(field)[:1])
                for field in container_fields
            }
            base_annotation_dict.update(annotation_dict)
        base_query = base_query.annotate(**base_annotation_dict)
        self._ts_queryset_containers = []
        base_query = base_query.order_by("-value_date", "-pk")
        return base_query

    def _get_extended_container_queryset(
        self, ts_queryset_container: TSQueryContainer, base_query: QuerySet
    ) -> QuerySet:
        # Find any elements that are in the base query but not in the container_query and add them to DB
        container_query = ts_queryset_container.queryset
        container_fields = ts_queryset_container.fields

        container_values = container_query.values_list("pk", "value_date")
        exclude_condition = Q()
        for pk, value_date in container_values:
            exclude_condition |= Q(pk=pk, value_date=value_date)
        missing_container_entries = (
            base_query.filter(value_date__isnull=False)
            .exclude(exclude_condition)
            .values_list("pk", "value_date")
        )
        if len(missing_container_entries) == 0:
            return container_query
        container_satellite_class = ts_queryset_container.satellite_class
        missing_entries = []
        for pk, value_date in missing_container_entries:
            missing_entry = container_satellite_class(
                hub_entity_id=pk,
                value_date=value_date,
                comment="Automatically added empty TS entry to align with other TS entries",
            )
            missing_entries.append(missing_entry)
        ts_queryset_container.satellite_class.objects.bulk_create(missing_entries)
        return self.build_time_series_queryset_container(
            container_satellite_class, container_fields
        ).queryset

    def rename_field(self, field: str, new_name: str):
        self.annotations[new_name] = self.annotations.pop(field)

    def std_delete_object(self, obj: MontrekHubABC):
        obj.state_date_end = timezone.now()
        obj.save()
        for satellite_class in self._primary_satellite_classes:
            satellite_class.objects.filter(hub_entity=obj).update(
                state_date_end=timezone.now()
            )

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
            hub_entity = self.hub_class(
                created_by_id=self.session_user_id, state_date_start=timezone.now()
            )
        return hub_entity

    def _raise_for_anonymous_user(self):
        if not self.session_user_id:
            raise PermissionDenied("User not authenticated!")

    def _raise_for_duplicated_entries(self, data_frame: pd.DataFrame):
        raise_error = False
        error_message = ""
        for satellite_class in self._primary_satellite_classes:
            identifier_fields = satellite_class.identifier_fields
            subset = [col for col in identifier_fields if col in data_frame.columns]
            if "hub_entity_id" in data_frame.columns:
                subset = ["hub_entity_id"]
                if "value_date" in data_frame.columns:
                    subset.append("value_date")
            if not subset:
                continue
            duplicated_entries = data_frame.duplicated(subset=subset)
            if duplicated_entries.any():
                raise_error = True
                error_message += f"Duplicated entries found for {satellite_class.__name__} with fields {identifier_fields}\n"
        if raise_error:
            raise ValueError(error_message)

    def _drop_duplicates(self, data_frame: pd.DataFrame) -> pd.DataFrame:
        satellite_columns = [c.name for c in self.std_satellite_fields()]
        satellite_columns = [
            c for c in satellite_columns + ["hub_entity_id"] if c in data_frame.columns
        ]

        duplicated_data_frame = data_frame.loc[:, satellite_columns].duplicated()
        no_of_duplicated_entries = duplicated_data_frame.sum()
        if no_of_duplicated_entries == 0:
            return data_frame
        self.messages.append(
            MontrekMessageWarning(
                f"{no_of_duplicated_entries} duplicated entries not uploaded!"
            )
        )
        return data_frame.loc[~(duplicated_data_frame)]

    def _drop_empty_rows(self, data_frame: pd.DataFrame) -> pd.DataFrame:
        dropped_data_frame = data_frame.dropna(how="all")
        dropped_data_frame = dropped_data_frame.convert_dtypes()
        dropped_rows = len(data_frame) - len(dropped_data_frame)
        if dropped_rows > 0:
            self.messages.append(
                MontrekMessageWarning(f"{dropped_rows} empty rows not uploaded!")
            )
            return dropped_data_frame
        return data_frame
