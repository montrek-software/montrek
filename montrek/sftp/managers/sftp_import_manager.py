import logging
import tempfile
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

import paramiko
from django.core.files import File
from django.utils import timezone

from baseclasses.errors.montrek_user_error import MontrekError
from baseclasses.managers.montrek_manager import MontrekManager
from baseclasses.repositories.db.typing import DataDict
from file_upload.managers.file_upload_manager import FileUploadManagerABC
from file_upload.modules.unattended_upload_registry import UnattendedUploadRegistry
from sftp.managers.sftp_client_manager import SftpClientManager, SftpEntry
from sftp.models.sftp_import_source_sat_models import SftpImportSourceStatusSatellite
from sftp.repositories.sftp_connection_repositories import SftpConnectionRepository
from sftp.repositories.sftp_import_source_repositories import (
    SftpImportedFileRepository,
    SftpImportSourceRepository,
)
from user.managers.user_manager import UserManager

logger = logging.getLogger(__name__)

PollStatus = SftpImportSourceStatusSatellite.PollStatus

# What a poll may run into: an unreachable or misconfigured server, a missing
# directory, a source pointing to an unregistered pipeline
SYNC_ERRORS: tuple[type[Exception], ...] = (
    MontrekError,
    paramiko.SSHException,
    OSError,
)
# What uploading a single file may run into, on top of the above; it fails
# that file only, the others are still imported
FILE_ERRORS: tuple[type[Exception], ...] = (*SYNC_ERRORS, ValueError, KeyError)


@dataclass
class SftpSyncResult:
    imported: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    error: str = ""

    @property
    def status(self) -> str:
        if self.error or self.failed:
            return PollStatus.FAILED
        return PollStatus.SUCCESS

    @property
    def message(self) -> str:
        if self.error:
            return f"Polling failed: {self.error}"
        parts = []
        if self.imported:
            parts.append(
                f"Imported {len(self.imported)} file(s): {', '.join(self.imported)}"
            )
        if self.failed:
            parts.append(f"Failed {len(self.failed)} file(s): {'; '.join(self.failed)}")
        return ". ".join(parts) or "No new files"


class SftpImportManager(MontrekManager):
    """Hand new files of an SFTP import source to its upload pipeline.

    session_data["pk"] is the source's hub id. A remote file is new unless its
    path, size and modification time are in the ledger of imported files, so a
    file replaced on the server under the same name is imported again. Runs
    without a request: without session_data["user_id"] it acts as superuser.
    """

    repository_class = SftpImportSourceRepository

    def __init__(self, session_data: DataDict | None = None):
        super().__init__(session_data)
        if not self.session_data.get("user_id"):
            self.session_data["user_id"] = UserManager().get_superuser().pk
        self.imported_file_repository = SftpImportedFileRepository(self.session_data)
        self.source: Any = None

    def sync(self) -> SftpSyncResult:
        self.source = self.repository.receive().get(hub_id=self.session_data["pk"])
        result = SftpSyncResult()
        try:
            manager_class = UnattendedUploadRegistry.get_manager_class(
                self.source.upload_type
            )
            with SftpClientManager({"pk": self._connection_pk()}) as client:
                self._sync_dir(client, manager_class, result)
        except SYNC_ERRORS as error:
            logger.warning("Polling SFTP import source %s failed", self.source.name)
            result.error = f"{type(error).__name__}: {error}"
        self._store_poll_status(result)
        return result

    def _sync_dir(
        self,
        client: SftpClientManager,
        manager_class: type[FileUploadManagerABC],
        result: SftpSyncResult,
    ) -> None:
        candidates = {
            self.import_key(entry): entry
            for entry in client.list_dir(self.source.remote_dir)
            if self._is_candidate(entry, manager_class)
        }
        imported_keys = self.imported_file_repository.get_imported_keys(candidates)
        for import_key, entry in candidates.items():
            if import_key in imported_keys:
                # Imported before, but moving it away failed then
                self._move_to_processed(client, entry)
                continue
            self._import_entry(client, manager_class, import_key, entry, result)

    def _is_candidate(
        self, entry: SftpEntry, manager_class: type[FileUploadManagerABC]
    ) -> bool:
        if entry.is_dir or not UnattendedUploadRegistry.accepts_file(
            manager_class, entry.name, self.source.file_pattern
        ):
            return False
        min_age = timedelta(seconds=self.source.min_file_age_seconds or 0)
        if entry.modified is None:
            # The age is unknown, so the file may still be being written
            return not min_age
        return entry.modified <= timezone.now() - min_age

    def import_key(self, entry: SftpEntry) -> str:
        modified = entry.modified.isoformat() if entry.modified else ""
        return f"{self.source.hub_id}|{entry.path}|{entry.size}|{modified}"

    def _import_entry(
        self,
        client: SftpClientManager,
        manager_class: type[FileUploadManagerABC],
        import_key: str,
        entry: SftpEntry,
        result: SftpSyncResult,
    ) -> None:
        try:
            registry_hub_id, message = self._upload(client, manager_class, entry)
        except FILE_ERRORS as error:
            # Not recorded as imported, so the next poll tries again
            logger.warning("Importing %s failed", entry.path)
            result.failed.append(f"{entry.name} ({type(error).__name__}: {error})")
            return
        self.imported_file_repository.create_by_dict(
            {
                "import_key": import_key,
                "remote_path": entry.path,
                "file_size": entry.size,
                "file_modified": entry.modified,
                "upload_type": self.source.upload_type,
                "registry_hub_id": registry_hub_id,
                "import_message": message,
                "link_sftp_imported_file_sftp_import_source": self.source.hub,
            }
        )
        result.imported.append(entry.name)
        # Moved once it is in the registry, whatever the pipeline made of it:
        # the registry keeps the file and reports how processing went
        self._move_to_processed(client, entry)

    def _upload(
        self,
        client: SftpClientManager,
        manager_class: type[FileUploadManagerABC],
        entry: SftpEntry,
    ) -> tuple[int | None, str]:
        pipeline_parameters = {
            **manager_class.unattended_default_parameters,
            **(self.source.pipeline_parameters or {}),
        }
        # Processors read the upload form's values from session_data
        upload_session_data = {
            "user_id": self.session_data["user_id"],
            **pipeline_parameters,
        }
        upload_manager = manager_class(session_data=upload_session_data)
        upload_manager.set_pipeline_data(pipeline_parameters)
        with tempfile.TemporaryDirectory() as local_dir:
            local_path = client.download_file(entry.path, local_dir)
            with local_path.open("rb") as file:
                # Stored in the media storage on registering, before the
                # temporary copy goes away
                upload_manager.upload_and_process(File(file, name=entry.name))
        registry_hub_id = upload_session_data.get(upload_manager.registry_session_key)
        return registry_hub_id, upload_manager.message

    def _move_to_processed(self, client: SftpClientManager, entry: SftpEntry) -> None:
        if not self.source.processed_dir:
            return
        try:
            client.move_file(entry.path, self.source.processed_dir)
        except SYNC_ERRORS as error:
            # Imported regardless; the ledger keeps it from being imported again
            logger.warning("Moving %s to processed failed: %s", entry.path, error)

    def _connection_pk(self) -> int:
        connection_hub_id = self.source.sftp_connection_hub_id
        if connection_hub_id is None:
            raise MontrekError(f"Import source {self.source.name} has no connection.")
        connection_repository = SftpConnectionRepository(self.session_data)
        return connection_repository.receive().get(hub_id=connection_hub_id).pk

    def _store_poll_status(self, result: SftpSyncResult) -> None:
        # Written only on a change: a poll every few minutes would otherwise
        # add a satellite version each time
        if (
            result.status == self.source.last_poll_status
            and result.message == self.source.last_poll_message
        ):
            return
        self.repository.create_by_dict(
            {
                "hub_entity_id": self.source.hub_id,
                "status_changed_at": timezone.now(),
                "last_poll_status": result.status,
                "last_poll_message": result.message,
            }
        )
