from api_upload.tests.factories import ApiUploadRegistryStaticSatelliteFactory
from django.test import TestCase

from api_upload.repositories.api_upload_registry_repository import (
    ApiUploadRepository,
)


class TestApiUploadRepository(TestCase):
    def test_std_queryset(self):
        ApiUploadRegistryStaticSatelliteFactory()
        queryset = ApiUploadRepository().receive()

        self.assertEqual(queryset.count(), 1)
