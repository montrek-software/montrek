import pandas as pd
from baseclasses.models import MontrekHubABC
from baseclasses.repositories.annotator import Annotator
from baseclasses.repositories.db.db_staller import DbStaller
from baseclasses.repositories.db.db_creator import DbCreator
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

    def create(self, data_frame: pd.DataFrame):
        self.data_frame = data_frame
        self._process_static_data()
        self.db_writer.write()

    def _process_static_data(self):
        static_columns = self.get_static_satellite_field_names()
        self._process_data(static_columns)

    def _process_data(self, columns: list[str]):
        data_frame = self.data_frame.loc[:, columns]
        data_frame.apply(self._process_row, axis=1)

    def _process_row(self, row: pd.Series):
        row_dict = row.to_dict()
        db_creator = DbCreator(self.db_staller, self.user_id)
        db_creator.create(row_dict)

    def get_static_satellite_field_names(self) -> list[str]:
        return self._get_satellite_field_names(is_time_series=False)

    def get_time_series_satellite_field_names(self) -> list[str]:
        return self._get_satellite_field_names(is_time_series=True)

    def _get_satellite_field_names(self, is_time_series: bool) -> list[str]:
        fields = []
        for satellite_class in self.annotator.annotated_satellite_classes:
            if satellite_class.is_timeseries == is_time_series:
                fields.extend(satellite_class.get_value_field_names())

        common_fields = ["hub_entity_id", "value_date"]
        sat_fields = list(set(fields)) + common_fields
        return [field for field in sat_fields if field in self.data_frame.columns]
