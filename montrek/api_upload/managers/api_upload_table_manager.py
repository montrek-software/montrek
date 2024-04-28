from api_upload.repositories.api_upload_registry_repository import (
    ApiUploadRepository,
)
from reporting.managers.montrek_table_manager import MontrekTableManager


class ApiUploadTableManager(MontrekTableManager):
    repository_class = ApiUploadRepository
