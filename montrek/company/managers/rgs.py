from typing import Dict
import pandas as pd
import datetime

from company.repositories.company_repository import CompanyRepository
from file_upload.models import FileUploadRegistryHub
from baseclasses.repositories.db_helper import new_satellite_entry
from company.models import (
    CompanyHub,
    CompanyStaticSatellite,
    CompanyTimeSeriesSatellite,
)


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

        identifier_hub_entity_map = {
            x: self.company_repository.std_create_object({"effectual_company_id": x})
            for x in df["effectual_company_id"].unique()
        }

        for hub_entity in identifier_hub_entity_map.values():
            hub_entity.link_company_file_upload_registry.add(
                self.file_upload_registry_hub
            )

        df_static = df[
            [
                "effectual_company_id",
                "company_name",
                "bloomberg_ticker",
            ]
        ].drop_duplicates()
        df_static.apply(
            lambda row: new_satellite_entry(
                CompanyStaticSatellite,
                identifier_hub_entity_map[row["effectual_company_id"]],
                **row.to_dict(),
            ),
            axis=1,
        )

        df_time_series = df[["effectual_company_id", "value_date", "total_revenue"]]
        df_time_series.apply(
            lambda row: new_satellite_entry(
                CompanyTimeSeriesSatellite,
                identifier_hub_entity_map[row["effectual_company_id"]],
                **{
                    k: v
                    for k, v in row.to_dict().items()
                    if k != "effectual_company_id"
                },
            ),
            axis=1,
        )

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
