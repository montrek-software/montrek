import pandas as pd


class RgsFileProcessor:
    def read_file(self, file_path: str) -> pd.DataFrame:
        cols = ["ticker", "total_revenue"]
        df = pd.read_excel(file_path)[cols]
        return df[cols]
