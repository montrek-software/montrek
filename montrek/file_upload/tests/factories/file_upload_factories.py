import os
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

import factory

from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekHubFactory,
    MontrekSatelliteFactory,
)


class FileUploadRegistryHubFactory(MontrekHubFactory):
    class Meta:
        model = "file_upload.FileUploadRegistryHub"


class FileUploadRegistryStaticSatelliteFactory(MontrekSatelliteFactory):
    class Meta:
        model = "file_upload.FileUploadRegistryStaticSatellite"

    hub_entity = factory.SubFactory(FileUploadRegistryHubFactory)
    file_name = factory.Faker("file_name", extension="csv")
    celery_task_id = factory.Faker("uuid4")

    @factory.post_generation
    def file_upload_file(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.hub_entity.link_file_upload_registry_file_upload_file.add(extracted)

    @factory.post_generation
    def generate_file_upload_file(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.test_file = SimpleUploadedFile(
                name=self.file_name,
                content=b"test",
                content_type="text/plain",
            )
            upload_file = FileUploadFileStaticSatelliteFactory.create(
                file=self.test_file
            )
            self.hub_entity.link_file_upload_registry_file_upload_file.add(
                upload_file.hub_entity
            )

    @factory.post_generation
    def generate_file_log_file(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.test_file = SimpleUploadedFile(
                name="test_file.txt",
                content=b"test",
                content_type="text/plain",
            )
            log_file = FileUploadFileStaticSatelliteFactory.create(file=self.test_file)
            self.hub_entity.link_file_upload_registry_file_log_file.add(
                log_file.hub_entity
            )


class FileUploadFileHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "file_upload.FileUploadFileHub"


class FileUploadFileStaticSatelliteFactory(MontrekSatelliteFactory):
    class Meta:
        model = "file_upload.FileUploadFileStaticSatellite"

    hub_entity = factory.SubFactory(FileUploadFileHubFactory)


def get_file_path(registry: FileUploadRegistryStaticSatelliteFactory) -> str:
    return os.path.join(
        settings.MEDIA_ROOT,
        str(registry.file_name),
    )
