from django.test import TestCase, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.core.files.uploadedfile import SimpleUploadedFile
from file_upload.tests.factories.file_upload_factories import (
    FileUploadRegistryStaticSatelliteFactory,
    FileUploadFileStaticSatelliteFactory,
)
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepository,
)

class TestFileUploadRegistryRepository(TestCase):
    def setUp(self):
        self.test_file = SimpleUploadedFile(
            name="test_file.txt",
            content="test".encode("utf-8"),
            content_type="text/plain",
        )
        self.file_registry_sat_factory = FileUploadRegistryStaticSatelliteFactory(
            file_name=self.test_file.name
        )
        self.file_file_sat_factory = FileUploadFileStaticSatelliteFactory(
            file=self.test_file
        )
        self.file_registry_sat_factory.hub_entity.link_file_upload_registry_file_upload_file.add(
            self.file_file_sat_factory.hub_entity
        )
        self.request = RequestFactory().get("/fake/")
        session_middleware = SessionMiddleware(lambda request: None)
        session_middleware.process_request(self.request)
        self.request.session.save()
        message_middleware = MessageMiddleware(lambda request: None)
        message_middleware.process_request(self.request)

    def test_get_file_from_registry(self):
        repository = FileUploadRegistryRepository()
        file_upload_registry = repository.std_queryset().first()
        test_file = repository.get_file_from_registry(file_upload_registry.id, self.request)
        expected_file = self.file_file_sat_factory.file
        self.assertEqual(test_file.read(), expected_file.read())

