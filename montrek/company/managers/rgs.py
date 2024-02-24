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
        df["hub_entity_id"] = self._create_or_update_company_hubs(
            df["bloomberg_ticker"]
        )
        self.company_repository.create_objects_from_data_frame(df)
        self.message = f"RGS upload was successfull (uploaded {df.shape[0]} rows.)"

    def _create_or_update_company_hubs(self, bloomberg_tickers: pd.Series) -> pd.Series:
        ticker_hub_entity_id_map = {}
        for bloomberg_ticker in bloomberg_tickers:
            company_hub = self.company_repository.std_create_object(
                {"bloomberg_ticker": bloomberg_ticker}
            )
            company_hub.link_company_file_upload_registry.add(
                self.file_upload_registry_hub
            )
            ticker_hub_entity_id_map[bloomberg_ticker] = company_hub.id
        return bloomberg_tickers.map(ticker_hub_entity_id_map)

    def _read_file(self, file_path: str) -> pd.DataFrame:
        read_cols = ["Year", "ticker", "total_revenue"]
        df = pd.read_excel(file_path, usecols=read_cols)
        return df

    def _pre_process_data(self, raw_df: pd.DataFrame):
        df = raw_df.copy()
        column_rename_map = {"ticker": "bloomberg_ticker", "Year": "year"}
        df = raw_df.rename(columns=column_rename_map)
        df["value_date"] = df["year"].apply(lambda x: datetime.date(x, 12, 31))
        drop_cols = ["year"]
        df = df.drop(columns=drop_cols)
        return df
