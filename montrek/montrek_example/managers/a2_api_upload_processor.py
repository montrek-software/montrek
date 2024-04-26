import pandas as pd
from montrek_example.repositories.hub_a_repository import HubARepository


class A2ApiUploadProcessor:
    message = "Not implemented"

    def __init__(self, file_upload_registry_id: int, session_data: dict, **kwargs):
        self.session_data = session_data

    def pre_check(self, json_response: dict | list) -> bool:
        return True

    def process(self, json_response: dict | list) -> bool:
        try:
            df = pd.DataFrame(json_response)
            HubARepository(self.session_data).create_objects_from_data_frame(df)
            self.message = f"Successfully saved {df.shape[0]} rows."
        except Exception as e:
            self.message = (
                f"Error raised during object creation: {e.__class__.__name__}: {e}"
            )
            return False
        return True

    def post_check(self, json_response: dict | list) -> bool:
        return True
