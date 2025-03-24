import pandas as pd
from data_import.base.managers.processor_base import ProcessorBaseABC
from montrek_example.repositories.hub_a_repository import HubARepository


class A2ApiUploadProcessor(ProcessorBaseABC):
    message = "Not implemented"


    def pre_check(self) -> bool:
        return True

    def process(self) -> bool:
        try:
            df = pd.DataFrame(self.import_data)
            HubARepository(self.session_data).create_objects_from_data_frame(df)
            self.message = f"Successfully saved {df.shape[0]} rows."
        except Exception as e:
            self.message = (
                f"Error raised during object creation: {e.__class__.__name__}: {e}"
            )
            return False
        return True

    def post_check(self) -> bool:
        return True
