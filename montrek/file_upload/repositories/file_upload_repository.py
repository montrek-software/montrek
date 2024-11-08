from baseclasses.repositories.montrek_repository import MontrekRepository
from file_upload.models import FileUploadFileHub


class FileUploadRepository(MontrekRepository):
    hub_class = FileUploadFileHub

    def add_annotations(self):
        pass
