import factory

from api_upload.models import (
    ApiUploadRegistryHub,
    ApiUploadRegistryStaticSatellite,
)
from baseclasses.tests.factories.montrek_factory_schemas import MontrekHubFactory


class ApiUploadRegistryHubFactory(MontrekHubFactory):
    class Meta:
        model = ApiUploadRegistryHub


class ApiUploadRegistryStaticSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ApiUploadRegistryStaticSatellite

    hub_entity = factory.SubFactory(ApiUploadRegistryHubFactory)
    url = factory.Faker("url")
    upload_status = ApiUploadRegistryStaticSatellite.UploadStatus.PROCESSED.value
    upload_message = factory.Faker("sentence")
