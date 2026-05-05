from django.conf import settings
import pandas as pd
from data_import.api_import.managers.api_data_import_processor import (
    ApiDataImportProcessorBase,
)
from montrek_example.managers.a2_request_manager import A2RequestManager
from montrek_example.repositories.hub_a_repository import HubARepository


class A2ApiUploadProcessor(ApiDataImportProcessorBase):
    message = "Not implemented"
    endpoint = "a2_endpoint"
    request_manager_class = A2RequestManager

    def process(self) -> bool:
        try:
            df = pd.DataFrame(self.import_data)
            HubARepository(self.session_data).create_objects_from_data_frame(df)
            self.message = f"Successfully saved {df.shape[0]} rows."
        except Exception as e:
            if settings.IS_TEST_RUN:
                raise e
            self.message = (
                f"Error raised during object creation: {e.__class__.__name__}: {e}"
            )
            return False
        return True

    def post_check(self) -> bool:
        return True
