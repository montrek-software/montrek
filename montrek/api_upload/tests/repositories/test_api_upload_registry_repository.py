from api_upload.tests.factories import ApiUploadRegistryStaticSatelliteFactory
from django.test import TestCase

from api_upload.repositories.api_upload_registry_repository import (
    ApiUploadRegistryRepository,
)


class TestApiUploadRegistryRepository(TestCase):
    def test_std_queryset(self):
        ApiUploadRegistryStaticSatelliteFactory()
        queryset = ApiUploadRegistryRepository().std_queryset()

        self.assertEqual(queryset.count(), 1)
