import pandas as pd
import datetime

from company.repositories.company_repository import CompanyRepository


class RgsFileProcessor:
    message = ""

    def __init__(self, company_repository: CompanyRepository):
        self.company_repository = company_repository

    def process(self, file_path: str):
        df = self._read_file(file_path)
        df = self._pre_process_data(df)
        df["hub_entity_id"] = self.get_company_hub_entity_ids(df["bloomberg_ticker"])
        self.company_repository.create_objects_from_data_frame(df)
        self.message = f"RGS upload was successfull (uploaded {df.shape[0]} rows.)"

    def get_company_hub_entity_ids(self, bloomberg_tickers: pd.Series) -> pd.Series:
        ticker_hub_entity_id_map = {
            t: self.company_repository.std_create_object({"bloomberg_ticker": t}).id
            for t in bloomberg_tickers.unique()
        }
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
