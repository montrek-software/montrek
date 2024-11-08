from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type

import pandas as pd
from baseclasses.dataclasses.montrek_message import (
    MontrekMessageWarning,
)
from baseclasses.errors.montrek_user_error import MontrekError
from baseclasses.models import (
    MontrekHubABC,
    MontrekLinkABC,
    MontrekSatelliteABC,
    MontrekTimeSeriesSatelliteABC,
)
from baseclasses.repositories.annotator import (
    Annotator,
)
from baseclasses.repositories.db_creator import DbCreator
from baseclasses.repositories.subquery_builder import (
    LastTSSatelliteSubqueryBuilder,
    LinkedSatelliteSubqueryBuilder,
    ReverseLinkedSatelliteSubqueryBuilder,
    SatelliteSubqueryBuilder,
)
from django.core.exceptions import PermissionDenied
from django.db.models import (
    F,
    ManyToManyField,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
)
from django.utils import timezone
from baseclasses.repositories.query_builder import QueryBuilder


@dataclass
class TSQueryContainer:
    queryset: QuerySet
    fields: List[str]
    satellite_class: type[MontrekTimeSeriesSatelliteABC]


class MontrekRepositoryOld:
    hub_class = MontrekHubABC

    def __init__(self, session_data: Dict[str, Any] = {}):
        self.annotator = Annotator(self.hub_class)
        self._primary_satellite_classes = []
        self._primary_link_classes = []
        self._ts_queryset_containers = []
        self.session_data = session_data
        self.query_builder = QueryBuilder(self.annotator, session_data)
        self._reference_date = None
        self.messages = []
        self.calculated_fields: list[str] = []
        self.linked_fields: list[str] = []

    @classmethod
    def get_hub_by_id(cls, pk: int) -> MontrekHubABC:
        return cls.hub_class.objects.get(pk=pk)

    @property
    def annotations(self):
        return self.annotator.annotations

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
        return self.annotator.satellite_fields()

    def _get_satellite_field_names(self, is_time_series: bool) -> list[str]:
        fields = []
        for satellite_class in self.annotator.annotated_satellite_classes:
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

    def get_all_fields(self) -> list[str]:
        return self.annotator.get_annotated_field_names() + self.calculated_fields

    def get_all_annotated_fields(self):
        return self.annotator.get_annotated_field_names()

    def std_create_object(self, data: Dict[str, Any]) -> MontrekHubABC:
        self._raise_for_anonymous_user()
        hub_entity = self._get_hub_from_data(data)
        db_creator = DbCreator(self.annotator)
        created_hub = db_creator.create(data, hub_entity, self.session_user_id)
        db_creator.save_stalled_objects()
        return created_hub

    @staticmethod
    def _convert_lists_to_tuples(df: pd.DataFrame, columns: List[str]):
        for col in columns:
            df[col] = df[col].apply(lambda x: tuple(x) if isinstance(x, list) else x)
        return df

    @staticmethod
    def _convert_tuples_to_lists(df: pd.DataFrame, columns: List[str]):
        for col in columns:
            df[col] = df[col].apply(lambda x: list(x) if isinstance(x, tuple) else x)
        return df

    def create_objects_from_data_frame(
        self, data_frame: pd.DataFrame
    ) -> List[MontrekHubABC]:
        self._raise_for_anonymous_user()
        static_fields = self.get_static_satellite_field_names()
        link_columns = [col for col in data_frame.columns if col.startswith("link_")]
        static_columns = [
            col for col in static_fields if col in data_frame.columns
        ] + link_columns
        ts_fields = self.get_time_series_satellite_field_names()
        ts_columns = [col for col in ts_fields if col in data_frame.columns]
        if static_columns:
            if ts_columns:
                # When static data and ts data is combined, the static data will be doubled in multiple lines
                # For cleaning purposes we drop duplicates here
                static_df = data_frame.loc[:, static_columns]
                static_df = self._convert_lists_to_tuples(static_df, link_columns)
                static_df = static_df.drop_duplicates()
                static_df = self._convert_tuples_to_lists(static_df, link_columns)
            else:
                static_df = data_frame.loc[:, static_columns]
            static_hubs = self._create_objects_from_data_frame(static_df)
        else:
            static_hubs = []
        if ts_columns:
            ts_hubs = self._create_objects_from_data_frame(
                data_frame.loc[:, ts_columns]
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
        db_creator = DbCreator(self.annotator)
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
            self.annotator.add_to_annotated_satellite_classes(satellite_class)
        else:
            self.annotator.subquery_builder_to_annotations(
                fields, satellite_class, SatelliteSubqueryBuilder
            )

    def add_last_ts_satellite_fields_annotations(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        fields: List[str],
    ):
        self.annotator.subquery_builder_to_annotations(
            fields,
            satellite_class,
            LastTSSatelliteSubqueryBuilder,
            end_date=self.session_end_date,
        )

    def add_linked_satellites_field_annotations(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        link_class: Type[MontrekLinkABC],
        fields: List[str],
        *,
        reversed_link: bool = False,
        last_ts_value: bool = False,
    ):
        if reversed_link:
            link_subquery_builder_class = ReverseLinkedSatelliteSubqueryBuilder
        else:
            link_subquery_builder_class = LinkedSatelliteSubqueryBuilder

        self.annotator.subquery_builder_to_annotations(
            fields,
            satellite_class,
            link_subquery_builder_class,
            link_class=link_class,
            last_ts_value=last_ts_value,
        )
        self._add_to_primary_link_classes(link_class)
        self.linked_fields.extend(fields)

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
        queryset = self.query_builder._apply_filter(queryset)
        # TODO: Add SubqueryBuilder for this when refactoring TS
        self.annotator.ts_annotations.update(field_map)  # Not nice, rework!

        return TSQueryContainer(
            queryset=queryset,
            fields=fields,
            satellite_class=time_series_satellite_class,
        )

    def get_history_queryset(self, pk: int, **kwargs) -> dict[str, QuerySet]:
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

    def get_hubs_by_field_values(
        self,
        values: list[Any],
        by_repository_field: str,
        *,
        raise_for_multiple_hubs: bool = True,
        raise_for_unmapped_values: bool = True,
    ) -> list[MontrekHubABC | None]:
        filter_kwargs = {f"{by_repository_field}__in": values}
        queryset = self.std_queryset().filter(**filter_kwargs)
        value_to_hub_map = {}
        unmapped_values = set()
        multiple_hub_values = set()
        hub_class_name = self.hub_class.__name__
        for obj in queryset:
            value = getattr(obj, by_repository_field)
            if value in value_to_hub_map:
                multiple_hub_values.add(value)
                continue
            value_to_hub_map[value] = obj
        if multiple_hub_values and raise_for_multiple_hubs:
            multiple_hubs_str = ", ".join(sorted(list(multiple_hub_values)[:10]))
            err_msg = f"Multiple {hub_class_name} objects found for {by_repository_field} values (truncated): {multiple_hubs_str}"
            raise MontrekError(err_msg)
        unmapped_values = set(values) - set(value_to_hub_map.keys())
        if raise_for_unmapped_values and unmapped_values:
            unmapped_values_str = ", ".join(sorted(list(unmapped_values)[:10]))
            err_msg = f"Cannot find {hub_class_name} objects for {by_repository_field} values (truncated): {unmapped_values_str}"
            raise MontrekError(err_msg)
        hubs = [value_to_hub_map.get(value) for value in values]
        return hubs

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


class MontrekRepository(MontrekRepositoryOld):
    # TODO: This is the facade for the repository refactor.
    # During the refactoring the dependency on MontrekRepositoryOld will be removed
    IS_REFACTORED = True  # Handles new refactoreed code, if True
    # TODO: Remove IS_REFACTORED
    update: bool = True  # If this is true only the passed fields will be updated, otherwise empty fields will be set to None
    default_order_fields: tuple[str, ...] = ()

    def __init__(self, session_data: Dict[str, Any] = {}):
        super().__init__(session_data)
        self.set_annotations()
        self._order_fields: tuple[str] | None = None

    # New methods

    def set_annotations(self):
        if self.IS_REFACTORED:
            raise NotImplementedError(
                f"set_annotations is not implemented for {self.__class__.__name__}"
            )
        self.std_queryset()

    def create_by_dict(self, data: Dict[str, Any]) -> MontrekHubABC:
        # Will replace std_create_object
        pass

    def create_by_data_frame(self, data_frame: pd.DataFrame) -> List[MontrekHubABC]:
        # Will replace create_objects_from_data_frame
        pass

    def receive(self) -> QuerySet:
        return self.query_builder.build_queryset(
            self.reference_date, self.order_fields()
        )

    def order_fields(self) -> tuple[str, ...]:
        if self._order_fields:
            return self._order_fields
        return self.default_order_fields

    def set_order_fields(self, fields: tuple[str]):
        self._order_fields = fields

    def delete(self, obj: MontrekHubABC):
        # Will replace std_delete_object
        pass
