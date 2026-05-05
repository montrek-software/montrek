from data_import.api_import.managers.api_data_import_manager import ApiDataImportManager
from montrek_example.managers.a2_api_upload_processor import (
    A2ApiUploadProcessor,
)
from montrek_example.repositories.hub_a_repository import HubAApiUploadRepository


class A2ApiUploadManager(ApiDataImportManager):
    registry_repository_class = HubAApiUploadRepository
    processor_class = A2ApiUploadProcessor
