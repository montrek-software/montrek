from api_upload.tests.factories import ApiUploadRegistryStaticSatelliteFactory
from django.test import TestCase

from api_upload.repositories.api_upload_registry_repository import (
    ApiUploadRepository,
    ApiUploadRepositoryABC,
)
from api_upload.models import ApiUploadRegistryHub


class MockApiUploadRepository(ApiUploadRepositoryABC):
    hub_class = ApiUploadRegistryHub


class TestApiUploadRepository(TestCase):
    def test_std_queryset(self):
        ApiUploadRegistryStaticSatelliteFactory()
        queryset = ApiUploadRepository().receive()

        self.assertEqual(queryset.count(), 1)

    def test_not_implemented_errors(self):
        self.assertRaises(NotImplementedError, ApiUploadRepositoryABC)
        self.assertRaises(NotImplementedError, MockApiUploadRepository)
