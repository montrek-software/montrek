from abc import ABC, abstractmethod

from api_upload.models import ApiUploadRegistryHub
from api_upload.repositories.api_upload_registry_repository import (
    ApiUploadRepository,
)
from baseclasses.dataclasses.montrek_message import (
    MontrekMessageError,
    MontrekMessageInfo,
)
from baseclasses.managers.montrek_manager import MontrekManager
from requesting.managers.request_manager import RequestManagerABC


class ApiUploadProcessorABC(ABC):
    message: str

    def __init__(
        self, api_upload_registry: ApiUploadRegistryHub, session_data: dict
    ) -> None:
        ...  # pragma: no cover

    @abstractmethod
    def pre_check(self, json_response: dict | list) -> bool:
        ...  # pragma: no cover

    @abstractmethod
    def process(self, json_response: dict | list) -> bool:
        ...  # pragma: no cover

    @abstractmethod
    def post_check(self, json_response: dict | list) -> bool:
        ...  # pragma: no cover


class ApiUploadManager(MontrekManager):
    repository_class = ApiUploadRepository
    request_manager_class: type[RequestManagerABC]
    api_upload_processor_class: type[ApiUploadProcessorABC]
    endpoint: str

    def __init__(
        self,
        session_data: dict,
    ) -> None:
        super().__init__(session_data=session_data)
        self.request_manager = self.request_manager_class(session_data)
        self.session_data = session_data
        self.registry_repository = self.repository_class(session_data)
        self.init_upload()
        self.processor = self.api_upload_processor_class(
            self.api_upload_registry, session_data
        )
        super().__init__(session_data=self.session_data)

    def upload_and_process(self) -> bool:
        response = self.request_manager.get_response(self.endpoint)
        us = self.registry_repository.upload_status
        if self.request_manager.status_code == 0:
            self._update_api_upload_registry(
                us.FAILED.value,
                self.request_manager.message,
            )
            return False
        if not self.processor.pre_check(response):
            self._update_api_upload_registry(us.FAILED.value, self.processor.message)
            return False
        if self.processor.process(response):
            if not self.processor.post_check(response):
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
                "url": self.get_url(),
                "upload_status": self.registry_repository.upload_status.PENDING.value,
                "upload_message": "Upload is pending",
            }
        )
        self.api_upload_registry = self.registry_repository.receive().get(
            hub__pk=api_upload_registry_hub.pk
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
        api_upload_registry_hub = self.registry_repository.std_create_object(att_dict)
        self.api_upload_registry = self.registry_repository.receive().get(
            hub__pk=api_upload_registry_hub.pk
        )

        if upload_status == self.registry_repository.upload_status.FAILED.value:
            self.messages.append(MontrekMessageError(upload_message))
        else:
            self.messages.append(MontrekMessageInfo(upload_message))

    def get_url(self) -> str:
        return self.request_manager.get_endpoint_url(self.endpoint)
