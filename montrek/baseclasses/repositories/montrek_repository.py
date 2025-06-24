from copy import deepcopy
import datetime
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type

import pandas as pd
from baseclasses.errors.montrek_user_error import MontrekError
from baseclasses.models import (
    HubValueDate,
    MontrekHubABC,
    MontrekLinkABC,
    MontrekSatelliteABC,
    MontrekSatelliteBaseABC,
    MontrekTimeSeriesSatelliteABC,
)
from baseclasses.repositories.annotator import (
    Annotator,
)
from baseclasses.repositories.db.db_creator import DataDict, DbCreator
from baseclasses.repositories.db.db_data_frame import DbDataFrame
from baseclasses.repositories.db.db_staller import DbStaller
from baseclasses.repositories.db.db_writer import DbWriter
from baseclasses.repositories.query_builder import QueryBuilder
from baseclasses.repositories.subquery_builder import (
    LinkedSatelliteSubqueryBuilder,
    ReverseLinkedSatelliteSubqueryBuilder,
    SatelliteSubqueryBuilder,
    SumTSSatelliteSubqueryBuilder,
    TSSatelliteSubqueryBuilder,
)
from baseclasses.utils import datetime_to_montrek_time
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import (
    F,
    QuerySet,
)
from django.utils import timezone

logger = logging.getLogger(__name__)


@dataclass
class TSQueryContainer:
    queryset: QuerySet
    fields: List[str]
    satellite_class: type[MontrekTimeSeriesSatelliteABC]


class MontrekRepository:
    hub_class = MontrekHubABC
    # default_order_fields: tuple[str, ...] = ("hub_id",)
    default_order_fields: tuple[str, ...] = ()
    latest_ts: bool = False
    view_model: None | type[models.Model] = None

    update: bool = True  # If this is true only the passed fields will be updated, otherwise empty fields will be set to None

    def __init__(self, session_data: Dict[str, Any] = {}):
        self.annotator = Annotator(self.hub_class)
        self._ts_queryset_containers = []
        self.session_data = session_data
        self.query_builder = QueryBuilder(self.annotator, session_data, self.latest_ts)
        self._reference_date = None
        self.messages = []
        self.calculated_fields: list[str] = []
        self.linked_fields: list[str] = []
        self.set_annotations()
        self._order_fields: tuple[str] | None = None

    def set_annotations(self):
        raise NotImplementedError(
            f"set_annotations is not implemented for {self.__class__.__name__}"
        )

    def create_by_dict(self, data: DataDict) -> MontrekHubABC:
        self._raise_for_anonymous_user()
        db_staller = DbStaller(self.annotator)
        db_creator = DbCreator(db_staller, self.session_user_id)
        db_creator.create(data)
        db_writer = DbWriter(db_staller)
        db_writer.write()
        self.store_in_view_model()
        return db_creator.hub

    def create_by_data_frame(self, data_frame: pd.DataFrame) -> List[MontrekHubABC]:
        self._raise_for_anonymous_user()
        db_data_frame = DbDataFrame(self.annotator, self.session_user_id)
        db_data_frame.create(data_frame)
        self.messages += db_data_frame.messages
        self.store_in_view_model()
        return db_data_frame.hubs

    def store_in_view_model(self):
        if not self.view_model:
            return

        query = self.receive_raw(update_view_model=True)
        self.store_query_in_view_model(query)

    def store_query_in_view_model(self, query):
        data = list(query.values())
        for row in data:
            if row["value_date"]:
                row["value_date"] = timezone.make_aware(
                    datetime.datetime.combine(row["value_date"], datetime.time()),
                    timezone.get_current_timezone(),
                )
        instances = [self.view_model(**item) for item in data]
        self.view_model.objects.all().delete()
        self.view_model.objects.bulk_create(instances, batch_size=1000)

    @classmethod
    def generate_view_model(cls):
        if cls.view_model:
            return

        class Meta:
            # Only works if repository is in repositories folder
            app_label = cls.__module__.split(".repositories")[0].split(".")[-1]
            managed = True
            db_table = f"{app_label}_{cls.__name__.lower()}_view_model"

        repo_instance = cls({})
        fields = repo_instance.annotator.get_annotated_field_map()
        for key, field in fields.items():
            field = deepcopy(field)
            field.null = True
            field.blank = True
            field.name = key
            fields[key] = field

        fields["value_date_list_id"] = models.IntegerField(null=True, blank=True)
        fields["hub"] = models.ForeignKey(cls.hub_class, on_delete=models.CASCADE)

        attrs = {
            "__module__": cls.__name__,
            "Meta": Meta,
            "reference_date": datetime.date.today(),
        }
        attrs.update(fields)
        model_name = cls.__name__ + "ViewModel"
        model = type(model_name, (models.Model,), attrs)

        cls.view_model = model  # Save the model class on the class

    def receive(self, apply_filter: bool = True) -> QuerySet:
        return self.receive_raw(apply_filter, False)

    def receive_raw(
        self, apply_filter: bool = True, update_view_model: bool = False
    ) -> QuerySet:
        if (
            self.view_model
            and not update_view_model
            and self.view_model.reference_date == self.reference_date.date()
        ):
            query = self.view_model.objects.all()
            if apply_filter:
                query_builder = QueryBuilder(self.annotator, self.session_data)
                query = query_builder._apply_order(query, self.order_fields())
                query = query_builder._apply_filter(query)
                return query
        query = self.query_builder.build_queryset(
            self.reference_date, self.order_fields(), apply_filter=apply_filter
        )
        if self.view_model:
            self.store_query_in_view_model(query)
        return query

    def delete(self, obj: MontrekHubABC):
        obj.state_date_end = timezone.now()
        obj.save()
        for satellite_class in self.annotator.get_satellite_classes():
            if satellite_class.is_timeseries:
                filter_kwargs = {"hub_value_date__hub": obj}
            else:
                filter_kwargs = {"hub_entity": obj}
            satellite_class.objects.filter(**filter_kwargs).update(
                state_date_end=timezone.now()
            )
        self.store_in_view_model()

    def order_fields(self) -> tuple[str, ...]:
        if self._order_fields:
            return self._order_fields
        return self.default_order_fields

    def set_order_fields(self, fields: tuple[str]):
        self._order_fields = fields

    @property
    def annotations(self):
        return self.annotator.annotations

    @property
    def reference_date(self) -> timezone.datetime:
        if self._reference_date is None:
            reference_date = self.session_data.get("reference_date", timezone.now())
            if isinstance(reference_date, list):
                reference_date = reference_date[0]
            if isinstance(reference_date, str):
                reference_date = datetime_to_montrek_time(
                    pd.to_datetime(reference_date)
                )
            return reference_date
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

    def object_to_dict(self, obj: HubValueDate) -> Dict[str, Any]:
        object_dict = {field: getattr(obj, field) for field in self.get_all_fields()}
        return object_dict

    def std_satellite_fields(self):
        return self.annotator.satellite_fields()

    def _get_satellite_field_names(self, is_time_series: bool) -> list[str]:
        fields = []
        for satellite_class in self.annotator.annotated_satellite_classes:
            if satellite_class.is_timeseries == is_time_series:
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
        return self.create_by_dict(data)

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
        return self.create_by_data_frame(data_frame)

    def add_satellite_fields_annotations(
        self,
        satellite_class: Type[MontrekSatelliteBaseABC],
        fields: List[str],
        *,
        rename_field_map: dict[str, str] = {},
        ts_agg_func: str | None = None,
    ):
        if satellite_class.is_timeseries:
            if ts_agg_func == "sum":
                subquery_builder = SumTSSatelliteSubqueryBuilder
            else:
                subquery_builder = TSSatelliteSubqueryBuilder
        else:
            subquery_builder = SatelliteSubqueryBuilder
        self.annotator.subquery_builder_to_annotations(
            fields, satellite_class, subquery_builder, rename_field_map=rename_field_map
        )

    def add_linked_satellites_field_annotations(
        self,
        satellite_class: Type[MontrekSatelliteABC | MontrekTimeSeriesSatelliteABC],
        link_class: Type[MontrekLinkABC],
        fields: List[str],
        *,
        reversed_link: bool = False,
        rename_field_map: dict[str, str] = {},
        parent_link_classes: tuple[Type[MontrekLinkABC], ...] = (),
        parent_link_reversed: tuple[bool] | list[bool] | None = None,
        agg_func: str = "string_concat",
        link_satellite_filter: dict[str, Any] = {},
        separator: str = ";",
    ):
        if reversed_link:
            link_subquery_builder_class = ReverseLinkedSatelliteSubqueryBuilder
        else:
            link_subquery_builder_class = LinkedSatelliteSubqueryBuilder
        if parent_link_reversed is None:
            parent_link_reversed = [reversed_link for _ in parent_link_classes]

        self.annotator.subquery_builder_to_annotations(
            fields,
            satellite_class,
            link_subquery_builder_class,
            link_class=link_class,
            rename_field_map=rename_field_map,
            parent_link_classes=parent_link_classes,
            parent_link_reversed=parent_link_reversed,
            agg_func=agg_func,
            link_satellite_filter=link_satellite_filter,
            separator=separator,
        )
        self.linked_fields.extend(fields)

    def get_history_queryset(self, pk: int, **kwargs) -> dict[str, QuerySet]:
        hub = self.get_hub_by_id(pk=pk)
        satellite_querys = {}
        for sat in self.annotator.get_satellite_classes():
            if sat.is_timeseries:
                sat_query = sat.objects.filter(hub_value_date__hub=hub).order_by(
                    ("-value_date")
                )
            else:
                sat_query = sat.objects.filter(hub_entity=hub).order_by("-created_at")
            sat_query = sat_query.annotate(
                changed_by=F("created_by__email"),
            )
            satellite_querys[sat.__name__] = sat_query
        for link in self.annotator.get_link_classes():
            hub_in_class = link.hub_in.field.remote_field.model
            if hub_in_class is self.hub_class:
                link_query = link.objects.filter(hub_in=hub)
            hub_out_class = link.hub_out.field.remote_field.model
            if hub_out_class is self.hub_class:
                link_query = link.objects.filter(hub_out=hub)
            link_query = link_query.order_by("-created_at")
            satellite_querys[link.__name__] = link_query
        return satellite_querys

    def rename_field(self, field: str, new_name: str):
        self.annotator.rename_field(field, new_name)

    def get_hubs_by_field_values(
        self,
        values: list[Any],
        by_repository_field: str,
        *,
        raise_for_multiple_hubs: bool = True,
        raise_for_unmapped_values: bool = True,
    ) -> list[MontrekHubABC | None]:
        filter_kwargs = {f"{by_repository_field}__in": values}
        queryset = self.receive().filter(**filter_kwargs)
        value_to_hub_map = {}
        unmapped_values = set()
        multiple_hub_values = set()
        hub_class_name = self.hub_class.__name__
        for obj in queryset:
            value = getattr(obj, by_repository_field)
            if value in value_to_hub_map:
                multiple_hub_values.add(value)
                continue
            value_to_hub_map[value] = obj.hub
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

    def get_hub_by_id(self, pk: int) -> MontrekHubABC:
        return self.hub_class.objects.get(hub_value_date__pk=pk)
