from typing import Any, Dict
from company.repositories.company_repository import CompanyRepository
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepository,
)
from company.managers.rgs import RgsFileProcessor


class CompanyFileUploadProcessor:
    message = "Not implemented"
    file_upload_registry = None

    def __init__(
        self, file_upload_registry_id: int, session_data: Dict[str, Any], **kwargs
    ):
        self.company_repository = CompanyRepository(session_data)

    def process(self, file_path: str):
        processor = RgsFileProcessor(self.company_repository)
        result = processor.process(file_path)
        self.message = processor.message
        return result

    def pre_check(self, file_path: str):
        return True

    def post_check(self, file_path: str):
        return True

    def _set_registry_to_company(
        self, company_hub_id: int, file_upload_registry_id: int
    ):
        file_upload_registry_hub = (
            FileUploadRegistryRepository()
            .std_queryset()
            .get(pk=file_upload_registry_id)
        )
        company_hub = CompanyRepository().std_queryset().get(pk=company_hub_id)
        company_hub.link_company_file_upload_registry.add(file_upload_registry_hub)
        return company_hub
