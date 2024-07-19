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
    MockFileUploadRegistryRepository,
    MockProcessFileTask,
)
from user.tests.factories.montrek_user_factories import MontrekUserFactory


class TestProcessFileTaskABC(TestCase):
    def setUp(self):
        self.task = MockProcessFileTask(
            file_upload_processor_class=MockFileUploadProcessor,
            file_upload_registry_repository_class=MockFileUploadRegistryRepository,
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
            "File processed" in m.body,
        )
        registry_sat_obj = MockFileUploadRegistryRepository({}).std_queryset().last()
        self.assertEqual(registry_sat_obj.upload_status, "processed")

    def test_run_error(self):
        registry_sat_obj = FileUploadRegistryStaticSatelliteFactory()
        file_path = f"/dummy/path/{registry_sat_obj.file_name}"
        self.task = ProcessFileTaskABC(
            file_upload_processor_class=MockFileUploadProcessorPostCheckFail,
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
            "Post check failed" in m.body,
        )
        registry_sat_obj = FileUploadRegistryRepository({}).std_queryset().last()
        self.assertEqual(registry_sat_obj.upload_status, "failed")
