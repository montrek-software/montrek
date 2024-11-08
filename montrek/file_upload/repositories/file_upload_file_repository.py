from baseclasses.repositories.montrek_repository import MontrekRepository
from file_upload.models import FileUploadFileHub
from file_upload.models import FileUploadFileStaticSatellite


class FileUploadFileRepository(MontrekRepository):
    hub_class = FileUploadFileHub

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            FileUploadFileStaticSatellite,
            ["file"],
        )
