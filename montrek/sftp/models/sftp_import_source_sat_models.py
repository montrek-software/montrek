from django.db import models

from baseclasses.models import MontrekSatelliteABC
from sftp.models.sftp_import_source_hub_models import (
    SftpImportedFileHub,
    SftpImportSourceHub,
)


class SftpImportSourceSatellite(MontrekSatelliteABC):
    """Which remote directory feeds which upload pipeline."""

    hub_entity = models.ForeignKey(SftpImportSourceHub, on_delete=models.CASCADE)

    name = models.CharField(max_length=255)
    remote_dir = models.CharField(
        max_length=1024,
        default=".",
        help_text="Directory to poll, relative to the connection's base path.",
    )
    file_pattern = models.CharField(
        max_length=255,
        default="*",
        help_text="Only files matching this glob are imported, e.g. '*.csv'.",
    )
    # Dotted path of an upload manager with allow_unattended_upload, see
    # file_upload.unattended_uploads; not a model choice, as the managers opt in
    # from their own apps
    upload_type = models.CharField(max_length=255)
    pipeline_parameters = models.JSONField(
        null=True,
        blank=True,
        help_text=(
            "What the pipeline would otherwise get from the upload form, "
            'e.g. {"overwrite": false}.'
        ),
    )
    min_file_age_seconds = models.PositiveIntegerField(
        default=60,
        help_text=(
            "Files modified more recently are skipped, as they may still be "
            "being written."
        ),
    )
    processed_dir = models.CharField(
        max_length=1024,
        blank=True,
        default="processed",
        help_text=(
            "Imported files are moved here, relative to the polled directory. "
            "Leave empty to keep them in place."
        ),
    )
    is_active = models.BooleanField(
        default=True, help_text="Only active sources are polled on schedule."
    )

    identifier_fields = ["name"]

    def __str__(self):
        return self.name


class SftpImportSourceStatusSatellite(MontrekSatelliteABC):
    """Outcome of the last poll; changes on every run, unlike the settings."""

    class PollStatus(models.TextChoices):
        NEVER = "never", "Never polled"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    hub_entity = models.ForeignKey(SftpImportSourceHub, on_delete=models.CASCADE)

    status_changed_at = models.DateTimeField(null=True, blank=True)
    last_poll_status = models.CharField(
        max_length=16, choices=PollStatus.choices, default=PollStatus.NEVER
    )
    last_poll_message = models.TextField(blank=True, default="")

    identifier_fields = ["hub_entity_id"]


class SftpImportedFileSatellite(MontrekSatelliteABC):
    """One imported version of a remote file.

    A file counts as imported by its path, size and modification time, so a
    file replaced on the server under the same name is imported again.
    """

    hub_entity = models.ForeignKey(SftpImportedFileHub, on_delete=models.CASCADE)

    # Source, path, size and mtime in one value: identifier fields cannot span
    # a link, and one indexed column keeps the "is it new?" lookup to one query
    import_key = models.CharField(max_length=1300, db_index=True)
    remote_path = models.CharField(max_length=1024)
    file_size = models.BigIntegerField()
    file_modified = models.DateTimeField(null=True, blank=True)
    upload_type = models.CharField(max_length=255)
    # Registries live in the apps of their pipelines, so no foreign key
    registry_hub_id = models.BigIntegerField(null=True, blank=True)
    import_message = models.TextField(blank=True, default="")

    identifier_fields = ["import_key"]

    def __str__(self):
        return self.remote_path
