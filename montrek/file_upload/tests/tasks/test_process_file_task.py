from django.core import mail
from file_upload.tests.factories.file_upload_factories import (
    FileUploadRegistryStaticSatelliteFactory,
)
from typing import Any
from django.test import TestCase

from file_upload.tasks.process_file_task import ProcessFileTaskBase
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepository,
)
from file_upload.models import FileUploadRegistryHubABC
from user.tests.factories.montrek_user_factories import MontrekUserFactory


class DummyFileUploadProcessor:
    message: str = ""

    def __init__(
        self,
        file_upload_registry_hub: FileUploadRegistryHubABC,
        session_data: dict[str, Any],
        **kwargs,
    ):
        pass

    def pre_check(self, file_path: str) -> bool:
        return True

    def process(self, file_path: str) -> bool:
        self.message = f"Successfully processed file '{file_path}'."
        return True

    def post_check(self, file_path: str) -> bool:
        return True


class ErrorFileUploadProcessor(DummyFileUploadProcessor):
    def post_check(self, file_path: str) -> bool:
        self.message = f"Post check failure for '{file_path}'."
        return False


class TestProcessFileTaskBase(TestCase):
    def setUp(self):
        self.task = ProcessFileTaskBase(
            file_upload_processor_class=DummyFileUploadProcessor,
            file_upload_registry_repository_class=FileUploadRegistryRepository,
        )
        self.user = MontrekUserFactory()
        self.session_data = {"user_id": self.user.id}

    def test_run(self):
        registry_sat_obj = FileUploadRegistryStaticSatelliteFactory()
        file_path = f"/dummy/path/{registry_sat_obj.file_name}"
        result = self.task.delay(
            file_path=file_path,
            file_upload_registry_id=registry_sat_obj.hub_entity.id,
            session_data=self.session_data,
        )
        self.assertTrue(result.successful())
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[0]
        self.assertEqual(m.to, [self.user.email])
        self.assertEqual(m.subject, "Backgroud File Upload Finished")
        self.assertTrue(
            f"Successfully processed file '{file_path}'." in m.body,
        )
        registry_sat_obj = FileUploadRegistryRepository({}).std_queryset().last()
        self.assertEqual(registry_sat_obj.upload_status, "processed")

    def test_run_error(self):
        registry_sat_obj = FileUploadRegistryStaticSatelliteFactory()
        file_path = f"/dummy/path/{registry_sat_obj.file_name}"
        self.task = ProcessFileTaskBase(
            file_upload_processor_class=ErrorFileUploadProcessor,
            file_upload_registry_repository_class=FileUploadRegistryRepository,
        )
        result = self.task.delay(
            file_path=file_path,
            file_upload_registry_id=registry_sat_obj.hub_entity.id,
            session_data=self.session_data,
        )
        self.assertTrue(result.successful())
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[0]
        self.assertEqual(m.to, [self.user.email])
        self.assertEqual(m.subject, "Backgroud File Upload Finished")
        self.assertTrue(
            f"Post check failure for '{file_path}'." in m.body,
        )
        registry_sat_obj = FileUploadRegistryRepository({}).std_queryset().last()
        self.assertEqual(registry_sat_obj.upload_status, "failed")
