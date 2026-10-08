from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_details_manager import MontrekDetailsManager
from reporting.managers.montrek_table_manager import MontrekTableManager
from sftp.repositories.sftp_import_source_repositories import (
    SftpImportSourceRepository,
    SftpSourceImportedFileRepository,
)


class CommonTableElementsMixin:
    @property
    def table_elements(self):
        return [
            te.StringTableElement(name="Name", attr="name"),
            te.StringTableElement(name="Host", attr="sftp_host"),
            te.StringTableElement(name="User", attr="sftp_user"),
            te.StringTableElement(name="Remote Dir", attr="remote_dir"),
            te.StringTableElement(name="File Pattern", attr="file_pattern"),
            te.StringTableElement(name="Upload Type", attr="upload_type"),
            te.BooleanTableElement(name="Active", attr="is_active"),
            te.StringTableElement(name="Last Poll Status", attr="last_poll_status"),
            te.TextTableElement(name="Last Poll Message", attr="last_poll_message"),
            te.DateTimeTableElement(name="Status Since", attr="status_changed_at"),
            te.PostActionTableElement(
                name="Sync",
                url="sftp_import_source_sync",
                icon="refresh",
                kwargs={"pk": "hub_id"},
                hover_text="Import new files now",
            ),
            te.LinkTableElement(
                name="Edit",
                url="sftp_import_source_update",
                icon="edit",
                kwargs={"pk": "id"},
                hover_text="Update Sftp Import Source",
            ),
            te.LinkTableElement(
                name="Delete",
                url="sftp_import_source_delete",
                icon="trash",
                kwargs={"pk": "id"},
                hover_text="Delete Sftp Import Source",
            ),
        ]


class SftpImportSourceTableManager(CommonTableElementsMixin, MontrekTableManager):
    repository_class = SftpImportSourceRepository

    @property
    def table_elements(self):
        table_elements = [
            te.LinkTextTableElement(
                name="Details",
                url="sftp_import_source_details",
                kwargs={"pk": "hub_id"},
                text="hub_entity_id",
                hover_text="View Sftp Import Source Details",
            ),
        ]
        table_elements += super().table_elements
        return table_elements


class SftpImportSourceDetailsManager(CommonTableElementsMixin, MontrekDetailsManager):
    repository_class = SftpImportSourceRepository

    @property
    def table_elements(self):
        table_elements = [
            te.StringTableElement(name="hub", attr="hub_entity_id"),
        ]
        table_elements += super().table_elements
        table_elements += [
            te.StringTableElement(name="Processed Dir", attr="processed_dir"),
            te.IntTableElement(name="Min File Age (s)", attr="min_file_age_seconds"),
            te.StringTableElement(
                name="Pipeline Parameters", attr="pipeline_parameters"
            ),
        ]
        return table_elements


class SftpImportedFileTableManager(MontrekTableManager):
    """The ledger of one source's imported files (session_data["pk"])."""

    repository_class = SftpSourceImportedFileRepository

    @property
    def table_elements(self):
        return [
            te.StringTableElement(name="Remote Path", attr="remote_path"),
            te.IntTableElement(name="Size (bytes)", attr="file_size"),
            te.DateTimeTableElement(name="Modified", attr="file_modified"),
            te.StringTableElement(name="Upload Type", attr="upload_type"),
            te.IntTableElement(name="Registry Id", attr="registry_hub_id"),
            te.TextTableElement(name="Message", attr="import_message"),
            te.DateTimeTableElement(name="Imported At", attr="created_at"),
        ]
