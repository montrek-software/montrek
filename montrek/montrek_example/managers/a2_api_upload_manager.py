from api_upload.managers.api_upload_manager import ApiUploadManager
from montrek_example.managers.a2_api_upload_processor import (
    A2ApiUploadProcessor,
)
from montrek_example.managers.a2_request_manager import A2RequestManager
from montrek_example.repositories.hub_a_repository import HubAApiUploadRepository


class A2ApiUploadManager(ApiUploadManager):
    repository_class = HubAApiUploadRepository
    endpoint = "a2_endpoint"
    request_manager_class = A2RequestManager
    api_upload_processor_class = A2ApiUploadProcessor
