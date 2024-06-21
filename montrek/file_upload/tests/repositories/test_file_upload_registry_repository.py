from django.utils import timezone
import datetime
from django.test import TestCase, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.core.files.uploadedfile import SimpleUploadedFile
from file_upload.tests.factories.file_upload_factories import (
    FileUploadRegistryStaticSatelliteFactory,
    FileUploadFileStaticSatelliteFactory,
)
from file_upload.tests.mocks import (
    MockFileUploadRegistryRepository,
    MockWrongHubClassFileUploadRegistryRepository,
    MockWrongStaticSatelliteClassFileUploadRegistryRepository,
    MockWrongLinkFileUploadRegistryRepository,
)
from user.tests.factories.montrek_user_factories import MontrekUserFactory


class TestFileUploadRegistryRepository(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()
        self.session_data = {"user_id": self.user.id}
        self.test_file = SimpleUploadedFile(
            name="test_file.txt",
            content="test".encode("utf-8"),
            content_type="text/plain",
        )
        self.file_registry_sat_factory = FileUploadRegistryStaticSatelliteFactory(
            file_name=self.test_file.name, upload_status="pending"
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
        repository = MockFileUploadRegistryRepository(self.session_data)
        file_upload_registry = repository.std_queryset().first()
        test_file = repository.get_file_from_registry(
            file_upload_registry.id, self.request
        )
        expected_file = self.file_file_sat_factory.file
        self.assertEqual(test_file.read(), expected_file.read())

    def test_std_queryset_upload_date(self):
        repository = MockFileUploadRegistryRepository(self.session_data)
        queryset = repository.std_queryset()
        first_upload_date = queryset.first().upload_date

        assert first_upload_date == self.file_registry_sat_factory.created_at

        repository.std_create_object(
            {
                "hub_entity_id": self.file_registry_sat_factory.hub_entity.id,
                "upload_status": "processed",
            }
        )
        queryset = repository.std_queryset()
        second_upload_date = queryset.first().upload_date

        assert second_upload_date > first_upload_date


class TestFileUploadRegistryRepositorySetUp(TestCase):
    def test_wrong_hub_class(self):
        with self.assertRaises(NotImplementedError):
            MockWrongHubClassFileUploadRegistryRepository()

    def test_wrong_static_satellite_class(self):
        with self.assertRaises(NotImplementedError):
            MockWrongStaticSatelliteClassFileUploadRegistryRepository()

    def test_wrong_link_file_upload_registry_file_upload_file_class(self):
        with self.assertRaises(NotImplementedError):
            MockWrongLinkFileUploadRegistryRepository()
