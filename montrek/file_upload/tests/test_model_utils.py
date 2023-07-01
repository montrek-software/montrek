from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from file_upload.model_utils import get_file_satellite_from_registry_satellite
from file_upload.tests.factories.file_upload_factories import FileUploadRegistryStaticSatelliteFactory
from file_upload.tests.factories.file_upload_factories import FileUploadFileStaticSatelliteFactory
from link_tables.tests.factories.link_tables_factories import FileUploadRegistryFileUploadFileLinkFactory

class UploadTransactionToAccountFileViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a file to upload
        txt_file_content = b'Test file content'
        cls.txt_file = SimpleUploadedFile('test_file.txt', txt_file_content)
        cls.file_registry_sat_factory = FileUploadRegistryStaticSatelliteFactory(
            file_name=cls.txt_file.name
        )
        cls.file_file_sat_factory = FileUploadFileStaticSatelliteFactory()
        file_registry_file_link_factory = FileUploadRegistryFileUploadFileLinkFactory(
            from_hub=cls.file_registry_sat_factory.hub_entity,
            to_hub=cls.file_file_sat_factory.hub_entity
        )



    def test_get_file_satellite_from_registry_satellite(self):
        self.file_file_sat_factory.file = self.txt_file
        self.file_file_sat_factory.save()
        file_sat = get_file_satellite_from_registry_satellite(self.file_registry_sat_factory)
        self.assertEqual(file_sat.file.name, 'uploads/test_file.txt')
