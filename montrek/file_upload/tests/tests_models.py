from django.test import TestCase

from file_upload.tests.factories.file_upload_factories import (
    FileUploadRegistryStaticSatelliteFactory
)
from file_upload.models import (
    FileUploadRegistryStaticSatellite
)

class TestFileUploadModels(TestCase):
    @classmethod
    def setUpTestData(cls):
        FileUploadRegistryStaticSatelliteFactory.create_batch(3)

    def test_file_upload_registry_static_satellite(self):
        self.assertEqual(FileUploadRegistryStaticSatellite.objects.count(), 3)
