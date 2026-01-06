import pandas as pd
from baseclasses.dataclasses.montrek_message import MontrekMessageWarning
from baseclasses.models import MontrekHubABC
from baseclasses.repositories.annotator import Annotator
from baseclasses.repositories.db.db_creator import DbBatchCreator, DbCreator
from baseclasses.repositories.db.db_staller import DbStaller
from baseclasses.repositories.db.db_writer import DbWriter

HubsList = list[MontrekHubABC]


class DbDataFrame:
    def __init__(self, annotator: Annotator, user_id: int):
        self.annotator = annotator
        self.user_id = user_id
        self.hubs: HubsList = []
        self.data_frame: pd.DataFrame = pd.DataFrame()
        self.db_staller = DbStaller(self.annotator)
        self.db_writer = DbWriter(self.db_staller)
        self.messages = []
        self.link_columns = []

    def create(self, data_frame: pd.DataFrame):
        if data_frame.empty:
            return
        self.data_frame = data_frame
        self._drop_empty_rows()
        self._drop_duplicates()
        self._process_static_data()
        self._process_time_series_data()
        self.db_writer.write()
        self._assign_hubs()

    def _process_static_data(self):
        self.link_columns = self.get_link_field_names()
        static_columns = self.get_static_satellite_field_names()
        static_columns.extend(self.link_columns)
        # If there are no static columns or only the hub, which is already there, skip data writing
        if len(static_columns) == 0 or static_columns == ["comment", "hub_entity_id"]:
            return
        self._process_data(static_columns)
        self.db_writer.write_hubs()

    def _process_time_series_data(self):
        self._set_missing_hubs()
        time_series_columns = self.get_time_series_satellite_field_names()
        allowed_fields = {"hub_entity_id", "comment"}
        if set(time_series_columns).issubset(allowed_fields):
            return
        self._process_data(time_series_columns)

    def _process_data(self, columns: list[str]):
        df = self.data_frame.loc[:, columns]

        df = self._convert_lists_to_tuples(df)
        df = df.drop_duplicates()
        df = self._convert_tuples_to_lists(df)

        # Must be done on the deduplicated frame
        self._raise_for_duplicated_entries(df)

        creator = DbBatchCreator(DbCreator(self.db_staller, self.user_id), df)
        creator.fill_data_collection()
        creator.create()
        hubs = dict(zip(df.index.tolist(), creator.hubs, strict=False))

        # Preserve original DataFrame shape semantics
        self.data_frame = self.data_frame.copy()
        self.data_frame["hub_entity"] = hubs

    def _convert_lists_to_tuples(self, df: pd.DataFrame):
        for col in self.link_columns:
            if col not in df.columns:
                continue
            df[col] = df[col].apply(lambda x: tuple(x) if isinstance(x, list) else x)
        return df

    def _convert_tuples_to_lists(self, df: pd.DataFrame):
        for col in self.link_columns:
            if col not in df.columns:
                continue
            df[col] = df[col].apply(lambda x: list(x) if isinstance(x, tuple) else x)
        return df

    def _assign_hubs(self):
        for hubs in self.db_writer.db_staller.get_hubs().values():
            self.hubs += hubs
        for hubs in self.db_writer.db_staller.get_updated_hubs().values():
            self.hubs += hubs
        for satellites in self.db_writer.db_staller.get_updated_satellites().values():
            hubs = [
                satellite.hub_entity
                for satellite in satellites
                if not satellite.is_timeseries
            ]
            hubs += [
                satellite.hub_value_date.hub
                for satellite in satellites
                if satellite.is_timeseries
            ]
            self.hubs += hubs

    def get_static_satellite_field_names(self) -> list[str]:
        return self._get_satellite_field_names(is_time_series=False)

    def get_time_series_satellite_field_names(self) -> list[str]:
        return self._get_satellite_field_names(is_time_series=True)

    def get_link_field_names(self) -> list[str]:
        fields = []
        for field in dir(self.annotator.hub_class):
            if field.startswith("link_"):
                fields.append(field)
        return [field for field in fields if field in self.data_frame.columns]

    def _get_satellite_field_names(self, is_time_series: bool) -> list[str]:
        fields = []
        for satellite_class in self.annotator.annotated_satellite_classes:
            if satellite_class.is_timeseries == is_time_series:
                fields.extend(satellite_class.get_value_field_names())
        if fields == []:
            return fields

        common_fields = ["hub_entity_id"]
        if is_time_series:
            common_fields.append("value_date")
        sat_fields = list(set(fields)) + common_fields
        return [field for field in sat_fields if field in self.data_frame.columns]

    def _raise_for_duplicated_entries(self, data_frame: pd.DataFrame):
        raise_error = False
        error_message = ""
        for satellite_class in self.annotator.get_satellite_classes():
            identifier_fields = satellite_class.identifier_fields
            identifier_field_names = [
                col for col in identifier_fields if col in data_frame.columns
            ]
            value_fields = satellite_class.get_value_field_names()
            value_field_names = [
                col for col in value_fields if col in data_frame.columns
            ]
            if "hub_entity_id" in data_frame.columns:
                value_field_names.append("hub_entity_id")
                identifier_field_names.append("hub_entity_id")
            if "value_date" in data_frame.columns:
                value_field_names.append("value_date")
                identifier_field_names.append("value_date")
            if not identifier_field_names:
                continue
            duplicated_entries = data_frame.loc[:, value_field_names].duplicated(
                subset=identifier_field_names
            )
            if duplicated_entries.any():
                raise_error = True
                error_message += f"Duplicated entries found for {satellite_class.__name__} with fields {identifier_fields}\n"
        if raise_error:
            raise ValueError(error_message)

    def _drop_duplicates(self):
        satellite_columns = [c.name for c in self.annotator.satellite_fields()]
        satellite_columns = [
            c
            for c in satellite_columns + ["hub_entity_id"]
            if c in self.data_frame.columns
        ]

        duplicated_data_frame = self.data_frame.loc[:, satellite_columns].duplicated()
        no_of_duplicated_entries = duplicated_data_frame.sum()
        if no_of_duplicated_entries == 0:
            return
        self.messages.append(
            MontrekMessageWarning(
                f"{no_of_duplicated_entries} duplicated entries not uploaded!"
            )
        )
        self.data_frame = self.data_frame.loc[~(duplicated_data_frame)]

    def _drop_empty_rows(self):
        dropped_data_frame = self.data_frame.dropna(how="all")
        dropped_data_frame = dropped_data_frame.convert_dtypes()
        dropped_rows = len(self.data_frame) - len(dropped_data_frame)
        if dropped_rows > 0:
            self.messages.append(
                MontrekMessageWarning(f"{dropped_rows} empty rows not uploaded!")
            )
            self.data_frame = dropped_data_frame

    def _assign_hub(self, x) -> int | None:
        if pd.isna(x):
            return None
        return x.pk

    def _set_missing_hubs(self):
        if "hub_entity_id" in self.data_frame.columns:
            return
        self.data_frame["hub_entity_id"] = self.data_frame["hub_entity"].apply(
            self._assign_hub
        )
        if not pd.isnull(self.data_frame["hub_entity"]).any():
            return
        static_identifier_fields = []
        for satellite_class in self.annotator.annotated_satellite_classes:
            if satellite_class.is_timeseries is False:
                static_identifier_fields.extend(satellite_class.identifier_fields)
        static_identifier_fields = [
            field
            for field in static_identifier_fields
            if field in self.data_frame.columns
        ]
        if not static_identifier_fields:
            return
        self.data_frame["hub_entity_id"] = self.data_frame.groupby(
            static_identifier_fields
        )["hub_entity_id"].transform(lambda x: x.ffill().bfill())
