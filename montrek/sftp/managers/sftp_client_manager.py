import io
import logging
import stat
from collections.abc import Callable, Iterator
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from types import TracebackType
from typing import Self

import paramiko

from baseclasses.errors.montrek_user_error import MontrekError
from baseclasses.managers.montrek_manager import MontrekManager
from baseclasses.repositories.db.typing import DataDict
from sftp.models.sftp_connection_sat_models import SftpCredentialSatellite
from sftp.repositories.sftp_connection_repositories import SftpConnectionRepository

logger = logging.getLogger(__name__)

# Tried in turn: paramiko cannot detect the type of a key given as text
PRIVATE_KEY_CLASSES: tuple[type[paramiko.PKey], ...] = (
    paramiko.Ed25519Key,
    paramiko.ECDSAKey,
    paramiko.RSAKey,
)

type ProgressCallback = Callable[[int, int], object]


class SftpError(MontrekError):
    """An SFTP connection cannot be set up as configured."""


@dataclass(frozen=True)
class SftpEntry:
    name: str
    # Absolute, so the entry can be downloaded from any working directory
    path: str
    is_dir: bool
    size: int
    modified: datetime | None

    @classmethod
    def from_attributes(
        cls, attributes: paramiko.SFTPAttributes, directory: str
    ) -> Self:
        modified = (
            datetime.fromtimestamp(attributes.st_mtime, tz=UTC)
            if attributes.st_mtime is not None
            else None
        )
        return cls(
            name=attributes.filename,
            path=_join(directory, attributes.filename),
            is_dir=_is_dir(attributes),
            size=attributes.st_size or 0,
            modified=modified,
        )


def _is_dir(attributes: paramiko.SFTPAttributes) -> bool:
    return attributes.st_mode is not None and stat.S_ISDIR(attributes.st_mode)


def _normalize_fingerprint(fingerprint: str) -> str:
    return fingerprint.strip().removeprefix("SHA256:").rstrip("=")


class FingerprintHostKeyPolicy(paramiko.MissingHostKeyPolicy):
    """Accept the server key only if it matches the stored SHA256 fingerprint.

    No known_hosts file is loaded, so paramiko consults this policy on every
    connect, before authenticating: a server that cannot be verified never
    receives the credentials. Only a trusted host may go without a fingerprint;
    a fingerprint that is configured is checked either way.
    """

    def __init__(self, expected_fingerprint: str, trusted_host: bool = False):
        self.expected_fingerprint = _normalize_fingerprint(expected_fingerprint)
        self.trusted_host = trusted_host

    def missing_host_key(
        self, client: paramiko.SSHClient, hostname: str, key: paramiko.PKey
    ) -> None:
        actual_fingerprint = key.fingerprint
        if not self.expected_fingerprint and self.trusted_host:
            logger.warning(
                "Host key of trusted host %s is not verified (%s): no "
                "fingerprint configured",
                hostname,
                actual_fingerprint,
            )
            return
        if not self.expected_fingerprint:
            raise SftpError(
                f"No host key fingerprint is configured for {hostname}, so its "
                f"identity cannot be verified (it presented {actual_fingerprint})."
            )
        if _normalize_fingerprint(actual_fingerprint) != self.expected_fingerprint:
            raise SftpError(
                f"Host key of {hostname} does not match the configured "
                f"fingerprint (got {actual_fingerprint})."
            )


class SftpClientManager(MontrekManager):
    """SFTP operations on a connection stored in the DB (session_data["pk"]).

    Every operation opens its own session; to run several operations over one
    connection, use the manager as a context manager:

        with SftpClientManager({"pk": pk}) as client:
            client.change_dir("/upload")
            entries = client.list_dir()
    """

    repository_class = SftpConnectionRepository

    def __init__(self, session_data: DataDict | None = None):
        super().__init__(session_data)
        self.sftp_credentials = self.get_object_from_pk(self.session_data["pk"])
        self._sftp: paramiko.SFTPClient | None = None
        self._exit_stack: ExitStack | None = None

    def __enter__(self) -> Self:
        with ExitStack() as exit_stack:
            self._sftp = exit_stack.enter_context(self.session())
            # Keep the session open beyond this block, until __exit__
            self._exit_stack = exit_stack.pop_all()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        exit_stack, self._exit_stack, self._sftp = self._exit_stack, None, None
        if exit_stack is not None:
            exit_stack.__exit__(exc_type, exc, traceback)

    @contextmanager
    def session(self) -> Iterator[paramiko.SFTPClient]:
        """Open an SSH connection and yield an SFTPClient; closes both afterwards."""
        credentials = self.sftp_credentials
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(
            FingerprintHostKeyPolicy(
                credentials.host_key_fingerprint or "",
                trusted_host=bool(credentials.trusted_host),
            )
        )
        try:
            ssh.connect(
                credentials.host,
                port=credentials.port,
                username=credentials.user,
                timeout=credentials.timeout_seconds,
                look_for_keys=False,
                allow_agent=False,
                **self._auth_kwargs(),
            )
            sftp = ssh.open_sftp()
            try:
                if credentials.base_path:
                    sftp.chdir(credentials.base_path)
                yield sftp
            finally:
                sftp.close()
        finally:
            ssh.close()

    def list_dir(self, path: str = ".") -> list[SftpEntry]:
        with self._client() as sftp:
            directory = sftp.normalize(path)
            entries = [
                SftpEntry.from_attributes(attributes, directory)
                for attributes in sftp.listdir_attr(path)
            ]
        return sorted(entries, key=lambda entry: entry.name)

    def change_dir(self, path: str) -> str:
        """Change the remote working directory and return the new absolute path.

        Only lasts as long as the session, so use it inside ``with manager:``.
        """
        with self._client() as sftp:
            sftp.chdir(path)
            return sftp.getcwd() or path

    def walk(self, path: str = ".") -> Iterator[tuple[str, list[str], list[str]]]:
        """Recursively yield (dirpath, dirnames, filenames), like os.walk."""
        with self._client() as sftp:
            yield from self._walk(sftp, path)

    def download_sftp_entry(
        self,
        sftp_entry: SftpEntry,
        local_dir: str | Path = ".",
    ) -> list[Path]:
        """Download an entry returned by list_dir, recursively for a directory."""
        if not sftp_entry.is_dir:
            return [self.download_file(sftp_entry.path, local_dir)]
        return self.download_dir(sftp_entry.path, local_dir)

    def download_file(
        self,
        remote_file: str,
        local_dir: str | Path = ".",
        callback: ProgressCallback | None = None,
    ) -> Path:
        """Download a single file into local_dir and return the local path."""
        local_dir = Path(local_dir)
        target = self._local_target(local_dir, PurePosixPath(remote_file).name)
        local_dir.mkdir(parents=True, exist_ok=True)
        with self._client() as sftp:
            sftp.get(remote_file, str(target), callback=callback)
        return target

    def download_dir(self, remote_dir: str, local_dir: str | Path = ".") -> list[Path]:
        """Recursively download a remote directory, preserving its structure.

        The files land in local_dir/<name of remote_dir>; returns their paths.
        """
        root = remote_dir.rstrip("/") or "/"
        base = Path(local_dir) / (PurePosixPath(root).name or "root")
        downloaded: list[Path] = []
        with self._client():
            for dirpath, _, filenames in self.walk(root):
                relative = PurePosixPath(dirpath).relative_to(root)
                target_dir = self._local_target(base, *relative.parts)
                for filename in filenames:
                    downloaded.append(
                        self.download_file(_join(dirpath, filename), target_dir)
                    )
        return downloaded

    def move_file(self, remote_file: str, target_dir: str) -> str:
        """Move a remote file into target_dir, creating it if missing.

        Returns the new path. Relative target dirs resolve against the file's
        directory, so "processed" means a sibling folder of the file.
        """
        source = PurePosixPath(remote_file)
        target_base = source.parent / target_dir
        target = target_base / source.name
        with self._client() as sftp:
            try:
                sftp.stat(str(target_base))
            except FileNotFoundError:
                sftp.mkdir(str(target_base))
            sftp.rename(str(source), str(target))
        return str(target)

    @contextmanager
    def _client(self) -> Iterator[paramiko.SFTPClient]:
        """Reuse the session of ``with manager:``, or open one for this call."""
        if self._sftp is not None:
            yield self._sftp
            return
        with self.session() as sftp:
            # Shared with the operations this one calls, e.g. by download_dir
            self._sftp = sftp
            try:
                yield sftp
            finally:
                self._sftp = None

    def _walk(
        self, sftp: paramiko.SFTPClient, path: str
    ) -> Iterator[tuple[str, list[str], list[str]]]:
        dirs: list[str] = []
        files: list[str] = []
        for attributes in sftp.listdir_attr(path):
            (dirs if _is_dir(attributes) else files).append(attributes.filename)
        yield path, dirs, files
        for dirname in dirs:
            yield from self._walk(sftp, _join(path, dirname))

    def _auth_kwargs(self) -> dict[str, object]:
        credentials = self.sftp_credentials
        auth_method = credentials.auth_method
        if auth_method == SftpCredentialSatellite.AuthMethod.PASSWORD:
            return {"password": credentials.password}
        if auth_method == SftpCredentialSatellite.AuthMethod.PRIVATE_KEY:
            return {"pkey": self._load_private_key()}
        raise SftpError(f"No credentials stored for SFTP connection {self._label}.")

    def _load_private_key(self) -> paramiko.PKey:
        credentials = self.sftp_credentials
        for key_class in PRIVATE_KEY_CLASSES:
            try:
                return key_class.from_private_key(
                    io.StringIO(credentials.private_key or ""),
                    password=credentials.private_key_passphrase or None,
                )
            except paramiko.SSHException:
                continue
        raise SftpError(
            f"The private key of SFTP connection {self._label} cannot be loaded: "
            "unsupported key type or wrong passphrase."
        )

    @property
    def _label(self) -> str:
        credentials = self.sftp_credentials
        return f"{credentials.user}@{credentials.host}:{credentials.port}"

    @staticmethod
    def _local_target(base: Path, *parts: str) -> Path:
        # Remote names come from the server, which must not be able to write
        # outside the target directory (e.g. with a file called "..")
        target = base.joinpath(*parts)
        if not target.resolve().is_relative_to(base.resolve()):
            raise SftpError(f"Refusing to write outside {base}: {target}")
        return target


def _join(dirpath: str, name: str) -> str:
    return f"{dirpath.rstrip('/')}/{name}"
