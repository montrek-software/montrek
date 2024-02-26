import pandas as pd
import datetime

from company.repositories.company_repository import CompanyRepository
from file_upload.models import FileUploadRegistryHub


class RgsFileProcessor:
    message = ""

    def __init__(
        self,
        company_repository: CompanyRepository,
        file_upload_registry_hub: FileUploadRegistryHub,
    ):
        self.company_repository = company_repository
        self.file_upload_registry_hub = file_upload_registry_hub

    def process(self, file_path: str):
        df = self._read_file(file_path)
        df = self._pre_process_data(df)

        df_static = df[
            [
                "company_name",
                "bloomberg_ticker",
                "effectual_company_id",
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
        }
        df = raw_df.rename(columns=column_rename_map)
        df["value_date"] = df["year"].apply(lambda x: datetime.date(x, 12, 31))
        drop_cols = ["year"]
        df = df.drop(columns=drop_cols)
        return df
