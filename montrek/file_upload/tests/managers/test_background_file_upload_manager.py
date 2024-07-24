from django.core import mail
from file_upload.tests.factories.file_upload_factories import (
    FileUploadRegistryStaticSatelliteFactory,
)
from typing import Any
from django.test import TestCase

from file_upload.tasks.process_file_task import ProcessFileTaskABC
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepository,
)
from file_upload.models import (
    FileUploadRegistryHubABC,
    FileUploadRegistryStaticSatellite,
)
from file_upload.managers.background_file_upload_manager import (
    BackgroundFileUploadManagerABC,
)
from file_upload.tests.mocks import (
    MockBackgroundFileUploadManager,
    MockFileUploadProcessorPreCheckFail,
    MockFileUploadRegistryRepository,
)
from user.tests.factories.montrek_user_factories import MontrekUserFactory
from django.core.files.uploadedfile import SimpleUploadedFile


class TestBackgroundFileUploadManagerABC(TestCase):
    def setUp(self):
        self.test_file = SimpleUploadedFile(
            name="test_file.txt",
            content="test".encode("utf-8"),
            content_type="text/plain",
        )
        self.user = MontrekUserFactory()
        self.session_data = {"user_id": self.user.id}

    def test_upload_and_process(self):
        manager = MockBackgroundFileUploadManager(
            file=self.test_file,
            session_data=self.session_data,
        )
        result = manager.upload_and_process()
        self.assertTrue(result)

        registry_sat_objects = FileUploadRegistryStaticSatellite.objects.all()
        upload_status = [
            o.upload_status for o in registry_sat_objects.order_by("updated_at")
        ]
        self.assertEqual(upload_status, ["pending", "scheduled", "processed"])

        registry_sat_obj = MockFileUploadRegistryRepository({}).std_queryset().last()
        self.assertEqual(registry_sat_obj.upload_status, "processed")
        self.assertEqual(
            manager.processor.message,
            "Upload background task scheduled. You will receive an email when the task is finished.",
        )
