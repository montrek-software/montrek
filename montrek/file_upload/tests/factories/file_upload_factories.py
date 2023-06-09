import factory

class FileUploadRegistryHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'file_upload.FileUploadRegistryHub'

class FileUploadRegistryStaticSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'file_upload.FileUploadRegistryStaticSatellite'
    hub_entity = factory.SubFactory(FileUploadRegistryHubFactory)
