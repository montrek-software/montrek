from django.core import mail
from file_upload.tests.factories.file_upload_factories import (
    FileUploadRegistryStaticSatelliteFactory,
)
from django.test import TestCase

from file_upload.tasks.process_file_task import ProcessFileTaskABC
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepository,
)
from file_upload.tests.mocks import (
    MockFileUploadProcessor,
    MockFileUploadProcessorPostCheckFail,
    MockFileUploadProcessorPreCheckFail,
    MockFileUploadRegistryRepository,
    MockProcessFileTask,
)
from user.tests.factories.montrek_user_factories import MontrekUserFactory


class MockPreCheckFailTask(ProcessFileTaskABC):
    file_upload_processor_class = MockFileUploadProcessorPreCheckFail
    file_upload_registry_repository_class = FileUploadRegistryRepository


class MockPostCheckFailTask(ProcessFileTaskABC):
    file_upload_processor_class = MockFileUploadProcessorPostCheckFail
    file_upload_registry_repository_class = FileUploadRegistryRepository


class ErrorFileUploadProcessor(MockFileUploadProcessor):
    def __init__(self, *args, **kwargs):
        raise RuntimeError("Processor error")


class MockErrorTask(ProcessFileTaskABC):
    file_upload_processor_class = ErrorFileUploadProcessor
    file_upload_registry_repository_class = FileUploadRegistryRepository


class TestProcessFileTaskABC(TestCase):
    def setUp(self):
        self.task = MockProcessFileTask()
        self.user = MontrekUserFactory()
        self.session_data = {"user_id": self.user.id}
        self.registry_sat_obj = FileUploadRegistryStaticSatelliteFactory()
        self.file_name = self.registry_sat_obj.file_name
        self.file_path = f"/dummy/path/{self.file_name}"

    def test_run(self):
        result = self.task.delay(
            file_path=self.file_path,
            file_upload_registry_id=self.registry_sat_obj.hub_entity.id,
            session_data=self.session_data,
        )
        self.assertTrue(result.successful())
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[0]
        self.assertEqual(m.to, [self.user.email])
        self.assertEqual(
            m.subject,
            f"Background file upload finished successfully. ({self.file_name})",
        )
        self.assertTrue(
            "File processed" in m.body,
        )
        registry_sat_obj = MockFileUploadRegistryRepository({}).receive().last()
        self.assertEqual(registry_sat_obj.upload_status, "processed")

    def test_run_pre_check_error(self):
        self.task = MockPreCheckFailTask()
        result = self.task.delay(
            file_path=self.file_path,
            file_upload_registry_id=self.registry_sat_obj.hub_entity.id,
            session_data=self.session_data,
        )
        self.assertTrue(result.successful())
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[0]
        self.assertEqual(m.to, [self.user.email])
        self.assertEqual(
            m.subject,
            f"ERROR: Background file upload did not finish successfully! ({self.file_name})",
        )
        self.assertTrue(
            "Pre check failed" in m.body,
        )
        registry_sat_obj = FileUploadRegistryRepository({}).receive().last()
        self.assertEqual(registry_sat_obj.upload_status, "failed")

    def test_run_post_check_error(self):
        self.task = MockPostCheckFailTask()
        result = self.task.delay(
            file_path=self.file_path,
            file_upload_registry_id=self.registry_sat_obj.hub_entity.id,
            session_data=self.session_data,
        )
        self.assertTrue(result.successful())
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[0]
        self.assertEqual(m.to, [self.user.email])
        self.assertEqual(
            m.subject,
            f"ERROR: Background file upload did not finish successfully! ({self.file_name})",
        )
        self.assertTrue(
            "Post check failed" in m.body,
        )
        registry_sat_obj = FileUploadRegistryRepository({}).receive().last()
        self.assertEqual(registry_sat_obj.upload_status, "failed")

    def test_run_unhandled_processor_error(self):
        self.task = MockErrorTask()
        result = self.task.delay(
            file_path=self.file_path,
            file_upload_registry_id=self.registry_sat_obj.hub_entity.id,
            session_data=self.session_data,
        )
        self.assertTrue(result.successful())
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[0]
        self.assertEqual(m.to, [self.user.email])
        self.assertEqual(
            m.subject,
            f"ERROR: Background file upload did not finish successfully! ({self.file_name})",
        )
        self.assertTrue(
            "Error raised during file processing: <br>RuntimeError: Processor error"
            in m.body,
        )
        registry_sat_obj = FileUploadRegistryRepository({}).receive().last()
        self.assertEqual(registry_sat_obj.upload_status, "failed")
