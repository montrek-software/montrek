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


class FileUploadFileHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "file_upload.FileUploadFileHub"


class FileUploadFileStaticSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "file_upload.FileUploadFileStaticSatellite"

    hub_entity = factory.SubFactory(FileUploadFileHubFactory)
