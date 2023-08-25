import hashlib
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from file_upload.tests.factories.file_upload_factories import (
    FileUploadRegistryStaticSatelliteFactory,
)
from file_upload.tests.factories.file_upload_factories import (
    FileUploadRegistryHubFactory,
)
from file_upload.tests.factories.file_upload_factories import FileUploadFileHubFactory
from file_upload.models import FileUploadRegistryStaticSatellite
from file_upload.models import FileUploadFileStaticSatellite
from file_upload.models import FileUploadRegistryHub


class TestFileUploadModels(TestCase):
    # @classmethod
    # def setUpTestData(cls):
    #    FileUploadRegistryStaticSatelliteFactory.create_batch(3)

    def test_file_upload_registry_static_satellite(self):
        for file_type in ("csv", "json", "xml", "xlsx", "xls", "txt"):
            fu_hub = FileUploadRegistryHub.objects.create()
            file_upload_registry_static_satellite = (
                FileUploadRegistryStaticSatellite.objects.create(
                    hub_entity=fu_hub,
                    file_name=f"test_file_name.{file_type}",
                )
            )
            self.assertEqual(
                file_upload_registry_static_satellite.file_name,
                f"test_file_name.{file_type}",
            )
            self.assertEqual(file_upload_registry_static_satellite.file_type, file_type)

    def test_file_upload_registry_static_satellite_type_none(self):
        fu_hub = FileUploadRegistryHub.objects.create()
        with self.assertRaises(IOError) as cm:
            FileUploadRegistryStaticSatellite.objects.create(
                hub_entity=fu_hub,
                file_name="test_file_name",
            )
        expected_message = 'File "test_file_name" has no file type'
        self.assertEqual(str(cm.exception), expected_message)

    def test_file_upload_registry_static_satellite_type_none_with_dot(self):
        fu_hub = FileUploadRegistryHub.objects.create()
        with self.assertRaises(IOError) as cm:
            FileUploadRegistryStaticSatellite.objects.create(
                hub_entity=fu_hub,
                file_name="test_file_name.",
            )
        expected_message = 'File type "" is not valid'
        self.assertEqual(str(cm.exception), expected_message)

    def test_file_upload_registry_static_satellite_type_invalid(self):
        fu_hub = FileUploadRegistryHub.objects.create()
        with self.assertRaises(IOError) as cm:
            FileUploadRegistryStaticSatellite.objects.create(
                hub_entity=fu_hub,
                file_name="test_file_name.invalid",
            )
        expected_message = 'File type "invalid" is not valid'
        self.assertEqual(str(cm.exception), expected_message)

    def test_file_upload_registry_static_satellite_upload_status(self):
        fu_hub = FileUploadRegistryHub.objects.create()
        file_upload_registry_static_satellite = (
            FileUploadRegistryStaticSatellite.objects.create(
                hub_entity=fu_hub,
                file_name="test_file_name.txt",
            )
        )
        self.assertEqual(file_upload_registry_static_satellite.upload_status, "pending")

    def test_file_upload_registry_static_satellite_identifier(self):
        file_name = "test_file_name.txt"
        file_type = "txt"
        fu_sat = FileUploadRegistryStaticSatellite.objects.create(
            file_name=file_name,
            file_type=file_type,
            hub_entity=FileUploadRegistryHubFactory(),
        )
        test_hash = hashlib.sha256((file_name + file_type).encode("utf-8")).hexdigest()
        self.assertEqual(fu_sat.hash_identifier, test_hash)

    def test_file_upload_file_static_satellite_identifier(self):
        txt_file_content = b"Test file content"
        txt_file = SimpleUploadedFile("test_file.txt", txt_file_content)
        ff_sat = FileUploadFileStaticSatellite.objects.create(
            file=txt_file,
            hub_entity=FileUploadFileHubFactory(),
        )
        test_hash = hashlib.sha256(
            (str(ff_sat.hub_entity_id)).encode("utf-8")
        ).hexdigest()
        self.assertEqual(ff_sat.hash_identifier, test_hash)
