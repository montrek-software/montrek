from collections.abc import Iterable

from django.db.models import QuerySet

from baseclasses.repositories.montrek_repository import MontrekRepository
from sftp.models.sftp_connection_sat_models import SftpConnectionSatellite
from sftp.models.sftp_import_source_hub_models import (
    LinkSftpImportedFileSftpImportSource,
    LinkSftpImportSourceSftpConnection,
    SftpImportedFileHub,
    SftpImportSourceHub,
)
from sftp.models.sftp_import_source_sat_models import (
    SftpImportedFileSatellite,
    SftpImportSourceSatellite,
    SftpImportSourceStatusSatellite,
)


class SftpImportSourceRepository(MontrekRepository):
    hub_class = SftpImportSourceHub

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            SftpImportSourceSatellite,
            [
                "name",
                "remote_dir",
                "file_pattern",
                "upload_type",
                "pipeline_parameters",
                "min_file_age_seconds",
                "processed_dir",
                "is_active",
            ],
        )
        self.add_satellite_fields_annotations(
            SftpImportSourceStatusSatellite,
            ["status_changed_at", "last_poll_status", "last_poll_message"],
        )
        self.add_linked_satellites_field_annotations(
            SftpConnectionSatellite,
            LinkSftpImportSourceSftpConnection,
            ["host", "user"],
            rename_field_map={"host": "sftp_host", "user": "sftp_user"},
        )
        self.add_linked_hub_id(
            LinkSftpImportSourceSftpConnection, "sftp_connection_hub_id"
        )

    def get_active_source_hub_ids(self) -> list[int]:
        return list(
            self.receive().filter(is_active=True).values_list("hub_id", flat=True)
        )


class SftpImportedFileRepository(MontrekRepository):
    hub_class = SftpImportedFileHub
    default_order_fields = ("-created_at",)

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            SftpImportedFileSatellite,
            [
                "import_key",
                "remote_path",
                "file_size",
                "file_modified",
                "upload_type",
                "registry_hub_id",
                "import_message",
                "created_at",
            ],
        )
        self.add_linked_hub_id(
            LinkSftpImportedFileSftpImportSource, "sftp_import_source_hub_id"
        )

    def get_imported_keys(self, import_keys: Iterable[str]) -> set[str]:
        """Which of the given keys are imported already, in one query."""
        return set(
            SftpImportedFileSatellite.objects.filter(
                import_key__in=list(import_keys)
            ).values_list("import_key", flat=True)
        )


class SftpSourceImportedFileRepository(SftpImportedFileRepository):
    """The imported files of the source in session_data["pk"] (its hub id)."""

    def receive(self, apply_filter: bool = True) -> QuerySet:
        return self.filter_by_linked_hub(
            super().receive(apply_filter),
            LinkSftpImportedFileSftpImportSource,
            self.session_data["pk"],
        )
