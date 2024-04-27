from typing import Protocol

from api_upload.repositories.api_upload_registry_repository import (
    ApiUploadRegistryRepository,
)
from baseclasses.models import MontrekHubABC
from baseclasses.managers.montrek_manager import MontrekManager
from api_upload.managers.request_manager import RequestManager
from baseclasses.dataclasses.montrek_message import (
    MontrekMessageError,
    MontrekMessageInfo,
)


# todo: should this be an ABC?
class ApiUploadProcessorProtocol(Protocol):
    message: str

    def __init__(
        self, api_upload_registry: MontrekHubABC, session_data: dict
    ) -> None: ...

    def pre_check(self, json_response: dict | list) -> bool: ...

    def process(self, json_response: dict | list) -> bool: ...

    def post_check(self, json_response: dict | list) -> bool: ...


class ApiUploadManager(MontrekManager):
    repository_class = ApiUploadRegistryRepository
    request_manager_class: type[RequestManager]
    api_upload_processor_class: type[ApiUploadProcessorProtocol]
    endpoint: str

    def __init__(
        self,
        session_data: dict,
    ) -> None:
        super().__init__(session_data=session_data)
        self.request_manager = self.request_manager_class()
        self.session_data = session_data
        self.registry_repository = self.repository_class(session_data)
        self.init_upload()
        self.processor = self.api_upload_processor_class(
            self.api_upload_registry, session_data
        )
        super().__init__(session_data=self.session_data)

    def upload_and_process(self) -> bool:
        json_response = self.request_manager.get_json(self.endpoint)
        us = self.registry_repository.upload_status
        if self.request_manager.status_code == 0:
            self._update_api_upload_registry(
                us.FAILED.value,
                self.request_manager.message,
            )
            return False
        if not self.processor.pre_check(json_response):
            self._update_api_upload_registry(us.FAILED.value, self.processor.message)
            return False
        if self.processor.process(json_response):
            if not self.processor.post_check(json_response):
                self._update_api_upload_registry(
                    us.FAILED.value, self.processor.message
                )
                return False
            self._update_api_upload_registry(us.PROCESSED.value, self.processor.message)
            return True
        else:
            self._update_api_upload_registry(us.FAILED.value, self.processor.message)
            return False

    def init_upload(self) -> None:
        api_upload_registry_hub = self.registry_repository.std_create_object(
            {
                "url": self.request_manager.get_endpoint_url(self.endpoint),
                "upload_status": self.registry_repository.upload_status.PENDING.value,
                "upload_message": "Upload is pending",
            }
        )
        self.api_upload_registry = self.registry_repository.std_queryset().get(
            pk=api_upload_registry_hub.pk
        )

    def _update_api_upload_registry(
        self, upload_status: str, upload_message: str
    ) -> None:
        att_dict = self.registry_repository.object_to_dict(self.api_upload_registry)
        att_dict.update(
            {
                "upload_status": upload_status,
                "upload_message": upload_message,
            },
        )
        self.api_upload_registry = self.registry_repository.std_create_object(att_dict)

        if upload_status == self.registry_repository.upload_status.FAILED.value:
            self.messages.append(MontrekMessageError(upload_message))
        else:
            self.messages.append(MontrekMessageInfo(upload_message))
