from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepository,
)
import pandas as pd
import datetime

from company.repositories.company_repository import CompanyRepository
from file_upload.models import FileUploadRegistryHub


class RgsFileProcessor:
    message = ""

    def __init__(
        self,
        session_data: dict,
        file_upload_registry_id: int,
    ):
        self.company_repository = CompanyRepository(session_data)
        self.file_upload_registry_repository = FileUploadRegistryRepository(
            session_data
        )
        self.file_upload_registry_hub = (
            self.file_upload_registry_repository.std_queryset().get(
                pk=file_upload_registry_id
            )
        )

    def process(self, file_path: str):
        df = self._read_file(file_path)
        df = self._pre_process_data(df)

        df_static = df[
            [
                "company_name",
                "bloomberg_ticker",
                "effectual_company_id",
                "share_class_figi",
            ]
        ].drop_duplicates()
        company_hubs = self.company_repository.create_objects_from_data_frame(df_static)
        df_static["hub_entity_id"] = [ch.id for ch in company_hubs]
        for ch in company_hubs:
            ch.link_company_file_upload_registry.add(self.file_upload_registry_hub)

        df["hub_entity_id"] = df["effectual_company_id"].map(
            df_static.set_index("effectual_company_id")["hub_entity_id"]
        )
        df_time_series = df[["hub_entity_id", "value_date", "total_revenue"]]
        self.company_repository.create_objects_from_data_frame(df_time_series)

        self.message = f"RGS upload was successfull (uploaded {df.shape[0]} rows)."
        return True

    def _read_file(self, file_path: str) -> pd.DataFrame:
        read_cols = [
            "Company_identifier",
            "Year",
            "name",
            "ticker",
            "total_revenue",
            "figi",
        ]
        df = pd.read_excel(file_path, usecols=read_cols)
        return df

    def _pre_process_data(self, raw_df: pd.DataFrame):
        df = raw_df.copy()
        column_rename_map = {
            "Company_identifier": "effectual_company_id",
            "Year": "year",
            "name": "company_name",
            "ticker": "bloomberg_ticker",
            "figi": "share_class_figi",
        }
        df = raw_df.rename(columns=column_rename_map)
        df["value_date"] = df["year"].apply(lambda x: datetime.date(x, 12, 31))
        drop_cols = ["year"]
        df = df.drop(columns=drop_cols)
        return df
