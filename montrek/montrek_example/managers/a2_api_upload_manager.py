from data_import.api_import.managers.api_data_import_manager import ApiDataImportManager
from montrek_example.managers.a2_api_upload_processor import (
    A2ApiUploadProcessor,
)
from montrek_example.managers.a2_request_manager import A2RequestManager
from montrek_example.repositories.hub_a_repository import HubAApiUploadRepository


class A2ApiUploadManager(ApiDataImportManager):
    registry_repository_class = HubAApiUploadRepository
    endpoint = "a2_endpoint"
    request_manager_class = A2RequestManager
    processor_class = A2ApiUploadProcessor
