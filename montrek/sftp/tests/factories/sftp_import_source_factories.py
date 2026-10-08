import factory

from baseclasses.tests.factories.baseclass_factories import ValueDateListFactory
from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekHubFactory,
    MontrekHubValueDateFactory,
    MontrekSatelliteFactory,
)
from sftp.models.sftp_import_source_hub_models import (
    LinkSftpImportedFileSftpImportSource,
    LinkSftpImportSourceSftpConnection,
    SftpImportedFileHub,
    SftpImportedFileHubValueDate,
    SftpImportSourceHub,
    SftpImportSourceHubValueDate,
)
from sftp.models.sftp_import_source_sat_models import (
    SftpImportedFileSatellite,
    SftpImportSourceSatellite,
)
from sftp.tests.factories.sftp_connection_hub_factories import SftpConnectionHubFactory

TEST_UPLOAD_TYPE = "file_upload.tests.mocks.MockUnattendedFileUploadManager"


class SftpImportSourceHubFactory(MontrekHubFactory):
    class Meta:
        model = SftpImportSourceHub


class SftpImportSourceHubValueDateFactory(MontrekHubValueDateFactory):
    class Meta:
        model = SftpImportSourceHubValueDate

    hub = factory.SubFactory(SftpImportSourceHubFactory)
    value_date_list = factory.SubFactory(ValueDateListFactory)


class SftpImportSourceSatelliteFactory(MontrekSatelliteFactory):
    class Meta:
        model = SftpImportSourceSatellite

    hub_entity = factory.SubFactory(SftpImportSourceHubFactory)
    name = factory.Sequence(lambda n: f"Import source {n}")
    remote_dir = "."
    file_pattern = "*"
    upload_type = TEST_UPLOAD_TYPE
    min_file_age_seconds = 60
    processed_dir = "processed"
    is_active = True


class LinkSftpImportSourceSftpConnectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LinkSftpImportSourceSftpConnection

    hub_in = factory.SubFactory(SftpImportSourceHubFactory)
    hub_out = factory.SubFactory(SftpConnectionHubFactory)


class SftpImportedFileHubFactory(MontrekHubFactory):
    class Meta:
        model = SftpImportedFileHub


class SftpImportedFileHubValueDateFactory(MontrekHubValueDateFactory):
    class Meta:
        model = SftpImportedFileHubValueDate

    hub = factory.SubFactory(SftpImportedFileHubFactory)
    value_date_list = factory.SubFactory(ValueDateListFactory)


class SftpImportedFileSatelliteFactory(MontrekSatelliteFactory):
    class Meta:
        model = SftpImportedFileSatellite

    hub_entity = factory.SubFactory(SftpImportedFileHubFactory)
    import_key = factory.Sequence(lambda n: f"key-{n}")
    remote_path = factory.Sequence(lambda n: f"/upload/file{n}.csv")
    file_size = 10
    upload_type = TEST_UPLOAD_TYPE


class LinkSftpImportedFileSftpImportSourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LinkSftpImportedFileSftpImportSource

    hub_in = factory.SubFactory(SftpImportedFileHubFactory)
    hub_out = factory.SubFactory(SftpImportSourceHubFactory)
