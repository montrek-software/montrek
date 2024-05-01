from api_upload.managers.api_upload_manager import ApiUploadManager
from montrek_example.managers.a2_api_upload_processor import (
    A2ApiUploadProcessor,
)
from montrek_example.managers.a2_request_manager import A2RequestManager


class A2ApiUploadManager(ApiUploadManager):
    endpoint = 'a2_endpoint'
    request_manager_class = A2RequestManager
    api_upload_processor_class = A2ApiUploadProcessor
