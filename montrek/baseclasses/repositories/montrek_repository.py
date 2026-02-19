import datetime
import logging
from dataclasses import dataclass
from typing import Any, cast
from collections.abc import Mapping

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
from baseclasses.repositories.annotator import Annotator
from baseclasses.repositories.db.db_creator import DataDict, DbCreator
from baseclasses.repositories.db.db_data_frame import DbDataFrame
from baseclasses.repositories.db.db_staller import DbStaller
from baseclasses.repositories.db.db_writer import DbWriter
from baseclasses.repositories.query_builder import QueryBuilder
from baseclasses.repositories.subquery_builder import (
    LinkedSatelliteSubqueryBuilder,
    ReverseLinkedSatelliteSubqueryBuilder,
    SatelliteSubqueryBuilder,
    TSSatelliteSubqueryBuilder,
)
from baseclasses.repositories.view_model_repository import ViewModelRepository
from baseclasses.typing import SessionDataType
from baseclasses.utils import (
    DJANGO_TO_PANDAS,
    PANDAS_DATETIME_PREFIX,
    PANDAS_MIN,
    datetime_to_montrek_time,
    django_field_to_pandas_dtype,
)
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import F, QuerySet
from django.utils import timezone
from django_pandas.io import read_frame

logger = logging.getLogger(__name__)


@dataclass
class TSQueryContainer:
    queryset: QuerySet
    fields: list[str]
    satellite_class: type[MontrekTimeSeriesSatelliteABC]


class MontrekRepository:
    hub_class = MontrekHubABC
    # default_order_fields: tuple[str, ...] = ("hub_id",)
    default_order_fields: tuple[str, ...] = ()
    latest_ts: bool = False
    view_model: None | type[models.Model] = None
    display_field_names: Mapping[str, str] = {}
    field_help_texts: Mapping[str, str] = {}

    update: bool = (
        True  # If this is true only the passed fields will be updated, otherwise empty fields will be set to None
    )

    def __init__(self, session_data: SessionDataType | None = None):
        self.annotator = Annotator(self.hub_class)
        self._ts_queryset_containers = []
        self.session_data = session_data if session_data is not None else {}
        self.query_builder = QueryBuilder(
            self.annotator, self.session_data, self.latest_ts
        )
        self._reference_date = None
        self.messages = []
        self.calculated_fields: list[str] = []
        self.linked_fields: list[str] = []
        self.set_annotations()
        self._order_fields: tuple[str] | None = None
        self._db_staller: DbStaller | None = None
        self.view_model_repository = ViewModelRepository(self.view_model)

    def set_annotations(self):
        raise NotImplementedError(
            f"set_annotations is not implemented for {self.__class__.__name__}"
        )

    def save_db_staller(self, db_staller: DbStaller):
        self._db_staller = db_staller

    def get_db_staller(self) -> DbStaller | None:
        return self._db_staller

    def create_by_dict(self, data: DataDict) -> MontrekHubABC:
        self._debug_logging("Start create by dict")
        self._raise_for_anonymous_user()
        db_staller = DbStaller(self.annotator)
        db_creator = DbCreator(db_staller, self.session_user_id)
        db_creator.create(data)
        db_writer = DbWriter(db_staller)
        db_writer.write()
        self.save_db_staller(db_staller)
        self.store_in_view_model(db_staller)
        self._debug_logging("End create by dict")
        return db_creator.hub

    def create_by_data_frame(self, data_frame: pd.DataFrame) -> list[MontrekHubABC]:
        self._debug_logging("raise for anonymous user")
        self._raise_for_anonymous_user()
        self._debug_logging("Get DbDataFrame")
        data_frame = self.skim_data_frame(data_frame)
        db_data_frame = DbDataFrame(self.annotator, self.session_user_id)
        self._debug_logging("Write to DB")
        db_data_frame.create(data_frame)
        self.messages += db_data_frame.messages
        self._debug_logging("Update view model")
        self.save_db_staller(db_data_frame.db_staller)
        self.store_in_view_model(db_data_frame.db_staller)
        self._debug_logging("Wrote data frame to DB")
        return db_data_frame.hubs

    def store_in_view_model(self, db_staller: DbStaller | None = None):
        if not self.view_model:
            return

        # When storing in the view model, we want to include all data without applying filters,
        # so we explicitly set apply_filter=False.
        query = self.receive_raw(update_view_model=True, apply_filter=False)
        self.view_model_repository.store_in_view_model(
            db_staller, query, self.hub_class
        )

    @classmethod
    def generate_view_model(cls):
        if cls.view_model:
            return
        repo_instance = cls({})
        fields = repo_instance.annotator.get_annotated_field_map()
        view_model = ViewModelRepository.generate_view_model(
            module_name=cls.__module__,
            repository_name=cls.__name__,
            hub_class=cls.hub_class,
            fields=fields,
        )
        cls.view_model = view_model  # Save the model class on the class

    def receive(self, apply_filter: bool = True) -> QuerySet:
        return self.receive_raw(apply_filter, False).select_related("hub")

    def receive_raw(
        self, apply_filter: bool = True, update_view_model: bool = False
    ) -> QuerySet:
        self._debug_logging("Start receive")
        if (
            self.view_model
            and not update_view_model
            and "reference_date" not in self.session_data
        ):
            return self.get_view_model_query(apply_filter=apply_filter)
        query = self.query_builder.build_queryset(
            self.reference_date, self.order_fields(), apply_filter=apply_filter
        )
        if self.view_model and not update_view_model:
            self.view_model_repository.store_query_in_view_model(query, "all")
        self._debug_logging("End receive")
        return query

    def get_view_model_query(self, apply_filter: bool = True) -> QuerySet:
        query = self.view_model.objects.all()
        if apply_filter:
            query_builder = QueryBuilder(self.annotator, self.session_data)
            query = query_builder._apply_order(query, self.order_fields())
            query = query_builder._apply_filter(query)
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
        self.delete_from_view_model(obj)

    def delete_from_view_model(self, obj: MontrekHubABC):
        self.view_model_repository.delete_from_view_model(obj)

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
    def session_user_id(self) -> int | None:
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

    def object_to_dict(self, obj: HubValueDate) -> dict[str, Any]:
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

    def get_all_annotated_fields(self) -> list[str]:
        return self.annotator.get_annotated_field_names()

    def get_link_names(self) -> list[str]:
        return [f.name for f in self.hub_class._meta.many_to_many]

    def std_create_object(self, data: dict[str, Any]) -> MontrekHubABC:
        return self.create_by_dict(data)

    @staticmethod
    def _convert_lists_to_tuples(df: pd.DataFrame, columns: list[str]):
        for col in columns:
            df[col] = df[col].apply(lambda x: tuple(x) if isinstance(x, list) else x)
        return df

    @staticmethod
    def _convert_tuples_to_lists(df: pd.DataFrame, columns: list[str]):
        for col in columns:
            df[col] = df[col].apply(lambda x: list(x) if isinstance(x, tuple) else x)
        return df

    def create_objects_from_data_frame(
        self, data_frame: pd.DataFrame
    ) -> list[MontrekHubABC]:
        return self.create_by_data_frame(data_frame)

    def add_satellite_fields_annotations(
        self,
        satellite_class: type[MontrekSatelliteBaseABC],
        fields: list[str],
        *,
        rename_field_map: dict[str, str] | None = None,
        ts_agg_func: str | None = None,
    ):
        if satellite_class.is_timeseries:
            subquery_builder = TSSatelliteSubqueryBuilder
        else:
            subquery_builder = SatelliteSubqueryBuilder
        rename_field_map = {} if rename_field_map is None else rename_field_map
        rename_field_map = cast(dict[str, str], rename_field_map)
        self.annotator.subquery_builder_to_annotations(
            fields,
            satellite_class,
            subquery_builder,
            rename_field_map=rename_field_map,
            ts_agg_func=ts_agg_func,
        )

    def add_linked_satellites_field_annotations(
        self,
        satellite_class: type[MontrekSatelliteABC | MontrekTimeSeriesSatelliteABC],
        link_class: type[MontrekLinkABC],
        fields: list[str],
        *,
        reversed_link: bool = False,
        rename_field_map: dict[str, str] | None = None,
        parent_link_classes: tuple[type[MontrekLinkABC], ...] = (),
        parent_link_reversed: tuple[bool] | list[bool] | None = None,
        agg_func: str = "string_concat",
        link_satellite_filter: dict[str, Any] | None = None,
        separator: str = ";",
    ):
        if reversed_link:
            link_subquery_builder_class = ReverseLinkedSatelliteSubqueryBuilder
        else:
            link_subquery_builder_class = LinkedSatelliteSubqueryBuilder
        if parent_link_reversed is None:
            parent_link_reversed = [reversed_link for _ in parent_link_classes]
        if len(parent_link_reversed) != len(parent_link_classes):
            raise ValueError(
                "'parent_link_classes' and 'parent_link_reversed' must have same length"
            )
        rename_field_map = {} if rename_field_map is None else rename_field_map
        rename_field_map = cast(dict[str, str], rename_field_map)
        link_satellite_filter = (
            {} if link_satellite_filter is None else link_satellite_filter
        )

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
                    "-value_date"
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

    def _get_hub_from_data(self, data: dict[str, Any]) -> MontrekHubABC:
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

    def _debug_logging(self, msg: str):
        logger.debug("%s: %s", self.__class__.__name__, msg)

    ## Return DF

    def get_df_dtypes(
        self,
        no_category_columns: list[str] | None = None,
    ) -> dict[str, str]:
        """
        Build a mapping from annotated model field names to pandas dtype strings.

        The fields considered are obtained from ``self.annotator.get_annotated_field_map()``.
        For each field, the dtype is determined using the following precedence rules:

        1. If the field defines ``choices``, its dtype is set to ``"category"`` regardless
           of the underlying Django field type.
        2. Otherwise, the field is matched against the ``DJANGO_TO_PANDAS`` mapping by
           ``isinstance(field, django_type)``; the first match provides the dtype.
        3. If no matching Django type is found, the dtype defaults to ``"object"``.

        Returns:
            dict[str, str]: A mapping where keys are annotated field names and values
            are pandas dtype names suitable for use when constructing a DataFrame.
        """
        field_map = self.annotator.get_annotated_field_map()
        dtypes: dict[str, str] = {}
        no_category_columns = [] if no_category_columns is None else no_category_columns

        for field_name, field in field_map.items():
            if field_name in no_category_columns:
                dtypes[field_name] = DJANGO_TO_PANDAS.get(type(field), "object")
            else:
                dtypes[field_name] = django_field_to_pandas_dtype(field)

        return dtypes

    def get_df(
        self,
        apply_filter: bool = True,
        columns: list[str] | None = None,
        no_category_columns: list[str] | None = None,
    ) -> pd.DataFrame:
        query = self.receive(apply_filter)
        return self.get_df_from_queryset(
            query,
            columns=columns,
            no_category_columns=no_category_columns,
        )

    def get_df_from_queryset(
        self,
        query: QuerySet,
        columns: list[str] | None = None,
        no_category_columns: list[str] | None = None,
    ) -> pd.DataFrame:
        columns = (
            self.get_all_annotated_fields() + ["id", "value_date_list_id"]
            if columns is None
            else columns
        )
        dtypes = self.get_df_dtypes(no_category_columns)
        dtypes = {k: v for k, v in dtypes.items() if k in columns}
        query = query.values(*columns)
        df = read_frame(query)
        df = self._normalize_min_dates(df, dtypes)
        df = df.astype(dtypes)
        df = self._apply_category_dtype(df, no_category_columns=no_category_columns)
        return df

    def skim_data_frame(self, data_frame: pd.DataFrame) -> pd.DataFrame:
        columns = self.get_all_annotated_fields() + self.get_link_names()
        columns = [col for col in columns if col in data_frame.columns]
        return data_frame.loc[:, columns]

    def _apply_category_dtype(
        self,
        df: pd.DataFrame,
        threshold: float = 0.10,
        no_category_columns: list[str] | None = None,
    ) -> pd.DataFrame:
        df = df.copy()

        no_category_columns = [] if no_category_columns is None else no_category_columns

        for col in df.columns:
            series = df[col]
            series = cast(pd.Series, series)
            if col in no_category_columns:
                continue

            if not pd.api.types.is_string_dtype(series):
                continue

            if self._should_use_category(series, threshold):
                df[col] = series.astype("category")

        return df

    def _should_use_category(self, series: pd.Series, threshold: float) -> bool:
        n = len(series)
        if n == 0:
            return False
        if series.isna().all():
            return False
        k = series.nunique(dropna=True)

        if k <= 20:
            return True

        return n >= 100 and (k / n) < threshold

    def _normalize_min_dates(
        self, df: pd.DataFrame, dtypes: dict[str, str]
    ) -> pd.DataFrame:
        df = df.copy()
        datetime_cols = [
            col for col, ty in dtypes.items() if self._is_datetime_dtype(ty)
        ]
        for col in datetime_cols:
            s = df[col]

            mask = s.isin([datetime.date.min, timezone.datetime.min])
            if bool(mask.any()):
                logger.warning(
                    f"Detected DB min dates in '{col}'; mapped to pandas min sentinel ({PANDAS_MIN})"
                )
                df[col] = s.where(~mask, PANDAS_MIN)

        return df

    def _is_datetime_dtype(self, dtype: str) -> bool:
        return dtype.startswith(PANDAS_DATETIME_PREFIX)
