from django.test import TestCase

from file_upload.tests.factories.file_upload_factories import (
    FileUploadRegistryStaticSatelliteFactory
)
from file_upload.models import (
    FileUploadRegistryStaticSatellite
)
from file_upload.models import (
    FileUploadRegistryHub
)

class TestFileUploadModels(TestCase):
    #@classmethod
    #def setUpTestData(cls):
    #    FileUploadRegistryStaticSatelliteFactory.create_batch(3)

    def test_file_upload_registry_static_satellite(self):
        for file_type in ('csv', 'json', 'xml', 'xlsx', 'xls', 'txt'):
            fu_hub = FileUploadRegistryHub.objects.create()
            file_upload_registry_static_satellite = (
                FileUploadRegistryStaticSatellite.objects.create(
                    hub_entity = fu_hub,
                    file_name = f'test_file_name.{file_type}',
                    file_path = 'test/file/path',
                    ))
            self.assertEqual(file_upload_registry_static_satellite.file_name, f'test_file_name.{file_type}')
            self.assertEqual(file_upload_registry_static_satellite.file_path, 'test/file/path')
            self.assertEqual(file_upload_registry_static_satellite.file_type, file_type)

    def test_file_upload_registry_static_satellite_type_none(self):
        fu_hub = FileUploadRegistryHub.objects.create()
        with self.assertRaises(IOError) as cm:
            FileUploadRegistryStaticSatellite.objects.create(
                hub_entity = fu_hub,
                file_name = 'test_file_name',
                file_path = 'test/file/path',
                )
        expected_message = 'File "test_file_name" has no file type'
        self.assertEqual(str(cm.exception), expected_message)

    def test_file_upload_registry_static_satellite_type_none_with_dot(self):
        fu_hub = FileUploadRegistryHub.objects.create()
        with self.assertRaises(IOError) as cm:
            FileUploadRegistryStaticSatellite.objects.create(
                hub_entity = fu_hub,
                file_name = 'test_file_name.',
                file_path = 'test/file/path',
                )
        expected_message = 'File type "" is not valid'
        self.assertEqual(str(cm.exception), expected_message)

    def test_file_upload_registry_static_satellite_type_invalid(self):
        fu_hub = FileUploadRegistryHub.objects.create()
        with self.assertRaises(IOError) as cm:
            FileUploadRegistryStaticSatellite.objects.create(
                hub_entity = fu_hub,
                file_name = 'test_file_name.invalid',
                file_path = 'test/file/path',
                )
        expected_message = 'File type "invalid" is not valid'
        self.assertEqual(str(cm.exception), expected_message)

    def test_file_upload_registry_static_satellite_path_invalid(self):
        fu_hub = FileUploadRegistryHub.objects.create()
        with self.assertRaises(IOError) as cm:
            FileUploadRegistryStaticSatellite.objects.create(
                hub_entity = fu_hub,
                file_name = 'test_file_name.txt',
                file_path = 'test/file/*path/with/invalid/characters/\\',
                )
        expected_message = 'File path is not valid\n\tfile path: test/file/*path/with/invalid/characters/\\'
        self.assertEqual(str(cm.exception), expected_message)

    def test_file_upload_registry_static_satellite_upload_status(self):
        fu_hub = FileUploadRegistryHub.objects.create()
        file_upload_registry_static_satellite = (
            FileUploadRegistryStaticSatellite.objects.create(
                hub_entity = fu_hub,
                file_name = 'test_file_name.txt',
                file_path = 'test/file/path',
                ))
        self.assertEqual(file_upload_registry_static_satellite.upload_status, 'pending')
