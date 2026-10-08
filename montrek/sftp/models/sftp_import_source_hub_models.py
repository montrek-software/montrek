from django.db import models

from baseclasses.fields import HubForeignKey
from baseclasses.models import HubValueDate, MontrekHubABC, MontrekOneToManyLinkABC
from sftp.models.sftp_connection_hub_models import SftpConnectionHub


class SftpImportSourceHub(MontrekHubABC):
    link_sftp_import_source_sftp_connection: models.ManyToManyField = (
        models.ManyToManyField(
            SftpConnectionHub,
            through="LinkSftpImportSourceSftpConnection",
            related_name="link_sftp_connection_sftp_import_source",
        )
    )


class SftpImportSourceHubValueDate(HubValueDate):
    hub = HubForeignKey(SftpImportSourceHub)


class LinkSftpImportSourceSftpConnection(MontrekOneToManyLinkABC):
    hub_in = models.ForeignKey(SftpImportSourceHub, on_delete=models.CASCADE)
    hub_out = models.ForeignKey(SftpConnectionHub, on_delete=models.CASCADE)


class SftpImportedFileHub(MontrekHubABC):
    link_sftp_imported_file_sftp_import_source: models.ManyToManyField = (
        models.ManyToManyField(
            SftpImportSourceHub,
            through="LinkSftpImportedFileSftpImportSource",
            related_name="link_sftp_import_source_sftp_imported_file",
        )
    )


class SftpImportedFileHubValueDate(HubValueDate):
    hub = HubForeignKey(SftpImportedFileHub)


class LinkSftpImportedFileSftpImportSource(MontrekOneToManyLinkABC):
    hub_in = models.ForeignKey(SftpImportedFileHub, on_delete=models.CASCADE)
    hub_out = models.ForeignKey(SftpImportSourceHub, on_delete=models.CASCADE)
