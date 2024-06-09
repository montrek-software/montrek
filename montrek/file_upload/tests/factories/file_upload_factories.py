from django.core.files.uploadedfile import SimpleUploadedFile
import factory


class FileUploadRegistryHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "file_upload.FileUploadRegistryHub"


class FileUploadRegistryStaticSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "file_upload.FileUploadRegistryStaticSatellite"

    hub_entity = factory.SubFactory(FileUploadRegistryHubFactory)
    file_name = factory.Faker("file_name", extension="csv")

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
                name="test_file.txt",
                content="test".encode("utf-8"),
                content_type="text/plain",
            )
            upload_file = FileUploadFileStaticSatelliteFactory.create(
                file=self.test_file
            )
            self.hub_entity.link_file_upload_registry_file_upload_file.add(
                upload_file.hub_entity
            )


class FileUploadFileHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "file_upload.FileUploadFileHub"


class FileUploadFileStaticSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "file_upload.FileUploadFileStaticSatellite"

    hub_entity = factory.SubFactory(FileUploadFileHubFactory)
