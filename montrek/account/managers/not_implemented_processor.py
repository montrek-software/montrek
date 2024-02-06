import pandas as pd


class NotImplementedFileUploadProcessor:
    message = "Not implemented"
    input_data_df = pd.DataFrame()

    def process(self, file_path: str) -> bool:
        return False

    def pre_check(self, file_path: str) -> bool:
        return False

    def post_check(self, file_path: str) -> bool:
        return False
