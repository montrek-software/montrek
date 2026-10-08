import copy
import io
import posixpath
import stat
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest import mock

import paramiko
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from django.test import TestCase

from sftp.managers.sftp_client_manager import (
    FingerprintHostKeyPolicy,
    SftpClientManager,
    SftpEntry,
    SftpError,
)
from sftp.tests.factories.sftp_connection_sat_factories import (
    TEST_HOST_FINGERPRINT,
    TEST_PASSPHRASE,
    TEST_PASSWORD,
    SftpConnectionSatelliteFactory,
    SftpCredentialSatelliteFactory,
)

MTIME = 1_700_000_000

# A directory is a dict, a file its content
REMOTE_TREE = {
    "upload": {
        "b.pdf": b"pdf content",
        "a.txt": b"text",
        "reports": {"2025": {"q1.csv": b"1,2,3"}, "summary.txt": b"sum"},
    },
}


class FakeSftpClient:
    """In-memory stand-in for paramiko.SFTPClient."""

    def __init__(self, tree: dict):
        # Copied, so a test editing the tree cannot leak into other tests
        self.tree = copy.deepcopy(tree)
        self.cwd = "/"
        self.closed = False

    def _resolve(self, path: str) -> str:
        return posixpath.normpath(posixpath.join(self.cwd, path))

    def _node(self, path: str):
        node = self.tree
        for part in self._resolve(path).strip("/").split("/"):
            if not part:
                continue
            if not isinstance(node, dict) or part not in node:
                raise FileNotFoundError(path)
            node = node[part]
        return node

    def listdir_attr(self, path: str = ".") -> list[paramiko.SFTPAttributes]:
        entries = []
        for name, node in self._node(path).items():
            attributes = paramiko.SFTPAttributes()
            attributes.filename = name
            is_dir = isinstance(node, dict)
            attributes.st_mode = (stat.S_IFDIR | 0o755) if is_dir else stat.S_IFREG
            attributes.st_size = 4096 if is_dir else len(node)
            attributes.st_mtime = MTIME
            entries.append(attributes)
        return entries

    def chdir(self, path: str) -> None:
        if not isinstance(self._node(path), dict):
            raise OSError(f"Not a directory: {path}")
        self.cwd = self._resolve(path)

    def normalize(self, path: str) -> str:
        self._node(path)
        return self._resolve(path)

    def getcwd(self) -> str:
        return self.cwd

    def get(self, remotepath: str, localpath: str, callback=None) -> None:
        content = self._node(remotepath)
        Path(localpath).write_bytes(content)
        if callback:
            callback(len(content), len(content))

    def stat(self, path: str) -> None:
        self._node(path)

    def mkdir(self, path: str) -> None:
        parent, name = posixpath.split(self._resolve(path))
        self._node(parent)[name] = {}

    def rename(self, old_path: str, new_path: str) -> None:
        old_parent, old_name = posixpath.split(self._resolve(old_path))
        new_parent, new_name = posixpath.split(self._resolve(new_path))
        target_dir = self._node(new_parent)
        if new_name in target_dir:
            # SFTP's rename never overwrites
            raise OSError(f"Failure: {new_path} exists")
        target_dir[new_name] = self._node(old_parent).pop(old_name)

    def close(self) -> None:
        self.closed = True


def _openssh_private_key(key: paramiko.PKey, passphrase: str | None) -> str:
    buffer = io.StringIO()
    key.write_private_key(buffer, password=passphrase)
    return buffer.getvalue()


class SftpClientManagerTestCase(TestCase):
    def setUp(self):
        self.connection = SftpConnectionSatelliteFactory(
            host="sftp.example.com",
            port=2222,
            user="alice",
            base_path="/upload",
            timeout_seconds=15,
        )
        self.credentials = SftpCredentialSatelliteFactory(
            hub_entity=self.connection.hub_entity, password=TEST_PASSWORD
        )
        self.fake_sftp = FakeSftpClient(REMOTE_TREE)
        ssh_client_patcher = mock.patch(
            "sftp.managers.sftp_client_manager.paramiko.SSHClient"
        )
        self.ssh_client_class = ssh_client_patcher.start()
        self.addCleanup(ssh_client_patcher.stop)
        self.ssh = self.ssh_client_class.return_value
        self.ssh.open_sftp.return_value = self.fake_sftp
        self.local_dir = Path(self.enterContext(tempfile.TemporaryDirectory()))

    def manager(self) -> SftpClientManager:
        return SftpClientManager({"pk": self.connection.get_hub_value_date().pk})

    def set_credentials(self, **kwargs):
        # Edit the stored row: a second satellite would duplicate the hub's rows
        for field, value in kwargs.items():
            setattr(self.credentials, field, value)
        self.credentials.save()


class TestSftpClientManagerSession(SftpClientManagerTestCase):
    def test_loads_connection_from_db(self):
        credentials = self.manager().sftp_credentials
        self.assertEqual(credentials.host, "sftp.example.com")
        self.assertEqual(credentials.password, TEST_PASSWORD)

    def test_connects_with_password(self):
        self.manager().list_dir()
        self.ssh.connect.assert_called_once_with(
            "sftp.example.com",
            port=2222,
            username="alice",
            timeout=15,
            look_for_keys=False,
            allow_agent=False,
            password=TEST_PASSWORD,
        )

    def test_verifies_host_key_with_stored_fingerprint(self):
        self.manager().list_dir()
        policy = self.ssh.set_missing_host_key_policy.call_args.args[0]
        self.assertIsInstance(policy, FingerprintHostKeyPolicy)
        self.assertEqual(
            policy.expected_fingerprint, TEST_HOST_FINGERPRINT.removeprefix("SHA256:")
        )
        self.assertFalse(policy.trusted_host)
        self.ssh.load_system_host_keys.assert_not_called()

    def test_passes_trusted_host_to_policy(self):
        self.connection.trusted_host = True
        self.connection.host_key_fingerprint = ""
        self.connection.save()
        self.manager().list_dir()
        policy = self.ssh.set_missing_host_key_policy.call_args.args[0]
        self.assertTrue(policy.trusted_host)
        self.assertEqual(policy.expected_fingerprint, "")

    def test_starts_in_base_path(self):
        with self.manager() as client:
            self.assertEqual(self.fake_sftp.getcwd(), "/upload")
            self.assertEqual(
                [entry.name for entry in client.list_dir()],
                ["a.txt", "b.pdf", "reports"],
            )

    def test_without_base_path_starts_in_server_default(self):
        self.connection.base_path = ""
        self.connection.save()
        self.manager().list_dir("/upload")
        self.assertEqual(self.fake_sftp.getcwd(), "/")

    def test_each_call_opens_and_closes_a_connection(self):
        manager = self.manager()
        manager.list_dir()
        manager.list_dir("reports")
        self.assertEqual(self.ssh.connect.call_count, 2)
        self.assertEqual(self.ssh.close.call_count, 2)
        self.assertTrue(self.fake_sftp.closed)

    def test_context_manager_reuses_one_connection(self):
        with self.manager() as client:
            client.list_dir()
            client.change_dir("reports")
            client.list_dir()
            self.ssh.close.assert_not_called()
        self.ssh.connect.assert_called_once()
        self.ssh.close.assert_called_once()
        self.assertTrue(self.fake_sftp.closed)

    def test_exit_without_enter_is_a_no_op(self):
        self.manager().__exit__(None, None, None)
        self.ssh.close.assert_not_called()

    def test_change_dir_lasts_for_the_session(self):
        with self.manager() as client:
            self.assertEqual(client.change_dir("reports"), "/upload/reports")
            self.assertEqual(
                [entry.name for entry in client.list_dir()], ["2025", "summary.txt"]
            )

    def test_connection_closed_after_error(self):
        with self.assertRaises(FileNotFoundError):
            self.manager().list_dir("missing")
        self.assertTrue(self.fake_sftp.closed)
        self.ssh.close.assert_called_once()

    def test_connection_closed_after_error_in_context_manager(self):
        with self.assertRaises(FileNotFoundError), self.manager() as client:
            client.list_dir("missing")
        self.ssh.close.assert_called_once()

    def test_ssh_closed_when_connect_fails(self):
        self.ssh.connect.side_effect = paramiko.AuthenticationException("denied")
        with self.assertRaises(paramiko.AuthenticationException):
            self.manager().list_dir()
        self.ssh.close.assert_called_once()
        self.ssh.open_sftp.assert_not_called()

    def test_without_credentials(self):
        connection = SftpConnectionSatelliteFactory(host="nocreds.example.com")
        manager = SftpClientManager({"pk": connection.get_hub_value_date().pk})
        with self.assertRaisesMessage(SftpError, "No credentials stored"):
            manager.list_dir()
        self.ssh.connect.assert_not_called()
        self.ssh.close.assert_called_once()


class TestSftpClientManagerPrivateKey(SftpClientManagerTestCase):
    def test_connects_with_encrypted_rsa_key(self):
        key = paramiko.RSAKey.generate(1024)
        self.set_credentials(
            auth_method="private_key",
            password=None,
            private_key=_openssh_private_key(key, TEST_PASSPHRASE),
            private_key_passphrase=TEST_PASSPHRASE,
        )

        self.manager().list_dir()

        connect_kwargs = self.ssh.connect.call_args.kwargs
        self.assertNotIn("password", connect_kwargs)
        self.assertEqual(connect_kwargs["pkey"].fingerprint, key.fingerprint)

    def test_connects_with_unencrypted_ed25519_key(self):
        private_key = (
            Ed25519PrivateKey.generate()
            .private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.OpenSSH,
                serialization.NoEncryption(),
            )
            .decode()
        )
        self.set_credentials(
            auth_method="private_key", password=None, private_key=private_key
        )

        self.manager().list_dir()

        pkey = self.ssh.connect.call_args.kwargs["pkey"]
        self.assertIsInstance(pkey, paramiko.Ed25519Key)

    def test_wrong_passphrase(self):
        key = paramiko.RSAKey.generate(1024)
        self.set_credentials(
            auth_method="private_key",
            password=None,
            private_key=_openssh_private_key(key, TEST_PASSPHRASE),
            private_key_passphrase="wrong",  # nosec B106 # noqa: S106 : test-only
        )
        with self.assertRaisesMessage(SftpError, "cannot be loaded"):
            self.manager().list_dir()
        self.ssh.connect.assert_not_called()

    def test_invalid_key(self):
        self.set_credentials(
            auth_method="private_key", password=None, private_key="not a key"
        )
        with self.assertRaisesMessage(SftpError, "alice@sftp.example.com:2222"):
            self.manager().list_dir()


class TestFingerprintHostKeyPolicy(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.key = paramiko.RSAKey.generate(1024)

    def test_accepts_matching_fingerprint(self):
        fingerprint = self.key.fingerprint
        for configured in (
            fingerprint,
            fingerprint.removeprefix("SHA256:"),
            f" {fingerprint}= ",
        ):
            with self.subTest(configured=configured):
                policy = FingerprintHostKeyPolicy(configured)
                policy.missing_host_key(mock.Mock(), "sftp.example.com", self.key)

    def test_rejects_other_fingerprint(self):
        other_key = paramiko.RSAKey.generate(1024)
        policy = FingerprintHostKeyPolicy(other_key.fingerprint)
        with self.assertRaisesMessage(SftpError, "does not match"):
            policy.missing_host_key(mock.Mock(), "sftp.example.com", self.key)

    def test_refuses_unverifiable_host_without_fingerprint(self):
        policy = FingerprintHostKeyPolicy("")
        with self.assertRaisesMessage(SftpError, "No host key fingerprint"):
            policy.missing_host_key(mock.Mock(), "sftp.example.com", self.key)

    def test_trusted_host_without_fingerprint_is_accepted_with_warning(self):
        policy = FingerprintHostKeyPolicy("", trusted_host=True)
        with self.assertLogs("sftp.managers.sftp_client_manager", "WARNING") as logs:
            policy.missing_host_key(mock.Mock(), "sftp.example.com", self.key)
        self.assertIn("not verified", logs.output[0])
        self.assertIn(self.key.fingerprint, logs.output[0])

    def test_trusted_host_still_checks_configured_fingerprint(self):
        other_key = paramiko.RSAKey.generate(1024)
        policy = FingerprintHostKeyPolicy(other_key.fingerprint, trusted_host=True)
        with self.assertRaisesMessage(SftpError, "does not match"):
            policy.missing_host_key(mock.Mock(), "sftp.example.com", self.key)
        FingerprintHostKeyPolicy(
            self.key.fingerprint, trusted_host=True
        ).missing_host_key(mock.Mock(), "sftp.example.com", self.key)


class TestSftpClientManagerOperations(SftpClientManagerTestCase):
    def test_list_dir(self):
        entries = self.manager().list_dir()
        modified = datetime.fromtimestamp(MTIME, tz=UTC)
        self.assertEqual(
            entries,
            [
                SftpEntry(
                    name="a.txt",
                    path="/upload/a.txt",
                    is_dir=False,
                    size=4,
                    modified=modified,
                ),
                SftpEntry(
                    name="b.pdf",
                    path="/upload/b.pdf",
                    is_dir=False,
                    size=11,
                    modified=modified,
                ),
                SftpEntry(
                    name="reports",
                    path="/upload/reports",
                    is_dir=True,
                    size=4096,
                    modified=modified,
                ),
            ],
        )

    def test_entry_without_size_and_mtime(self):
        attributes = paramiko.SFTPAttributes()
        attributes.filename = "unknown"
        self.assertEqual(
            SftpEntry.from_attributes(attributes, "/"),
            SftpEntry(
                name="unknown", path="/unknown", is_dir=False, size=0, modified=None
            ),
        )

    def test_list_dir_entries_have_absolute_paths(self):
        manager = self.manager()
        self.assertEqual(
            [entry.path for entry in manager.list_dir("reports/2025")],
            ["/upload/reports/2025/q1.csv"],
        )
        self.assertEqual([entry.path for entry in manager.list_dir("/")], ["/upload"])

    def test_walk(self):
        walked = [
            (dirpath, sorted(dirs), sorted(files))
            for dirpath, dirs, files in self.manager().walk("/upload")
        ]
        self.assertEqual(
            walked,
            [
                ("/upload", ["reports"], ["a.txt", "b.pdf"]),
                ("/upload/reports", ["2025"], ["summary.txt"]),
                ("/upload/reports/2025", [], ["q1.csv"]),
            ],
        )
        self.ssh.connect.assert_called_once()

    def test_download_file(self):
        callback = mock.Mock()
        target_dir = self.local_dir / "new"

        target = self.manager().download_file("b.pdf", target_dir, callback=callback)

        self.assertEqual(target, target_dir / "b.pdf")
        self.assertEqual(target.read_bytes(), b"pdf content")
        callback.assert_called_once_with(11, 11)

    def test_download_dir(self):
        downloaded = self.manager().download_dir("/upload/reports/", self.local_dir)

        base = self.local_dir / "reports"
        self.assertEqual(
            sorted(downloaded), [base / "2025" / "q1.csv", base / "summary.txt"]
        )
        self.assertEqual((base / "2025" / "q1.csv").read_bytes(), b"1,2,3")
        self.ssh.connect.assert_called_once()

    def test_download_root_dir(self):
        self.fake_sftp.tree = {"upload": {}, "top.txt": b"top"}
        downloaded = self.manager().download_dir("/", self.local_dir)
        self.assertEqual(downloaded, [self.local_dir / "root" / "top.txt"])

    def test_download_refuses_to_write_outside_target(self):
        self.fake_sftp.tree = {"upload": {"..": b"evil"}}
        with self.assertRaisesMessage(SftpError, "Refusing to write outside"):
            self.manager().download_dir("/upload", self.local_dir)
        self.assertEqual(list(self.local_dir.iterdir()), [])


class TestSftpClientManagerDownloadSftpEntry(SftpClientManagerTestCase):
    def _entry(self, manager: SftpClientManager, path: str, name: str) -> SftpEntry:
        return next(entry for entry in manager.list_dir(path) if entry.name == name)

    def test_downloads_file_entry(self):
        manager = self.manager()
        entry = self._entry(manager, ".", "b.pdf")

        downloaded = manager.download_sftp_entry(entry, self.local_dir)

        self.assertEqual(downloaded, [self.local_dir / "b.pdf"])
        self.assertEqual(downloaded[0].read_bytes(), b"pdf content")

    def test_downloads_directory_entry_recursively(self):
        manager = self.manager()
        entry = self._entry(manager, ".", "reports")

        downloaded = manager.download_sftp_entry(entry, self.local_dir)

        base = self.local_dir / "reports"
        self.assertEqual(
            sorted(downloaded), [base / "2025" / "q1.csv", base / "summary.txt"]
        )

    def test_downloads_entry_listed_from_subdirectory(self):
        manager = self.manager()
        entry = self._entry(manager, "reports/2025", "q1.csv")

        downloaded = manager.download_sftp_entry(entry, self.local_dir)

        self.assertEqual(downloaded[0].read_bytes(), b"1,2,3")

    def test_does_not_confuse_entries_with_same_name(self):
        self.fake_sftp.tree["upload"]["summary.txt"] = b"other file"
        manager = self.manager()
        entry = self._entry(manager, "reports", "summary.txt")

        downloaded = manager.download_sftp_entry(entry, self.local_dir)

        self.assertEqual(downloaded[0].read_bytes(), b"sum")

    def test_entry_survives_change_of_working_directory(self):
        with self.manager() as client:
            entry = self._entry(client, ".", "a.txt")
            client.change_dir("reports/2025")

            downloaded = client.download_sftp_entry(entry, self.local_dir)

        self.assertEqual(downloaded[0].read_bytes(), b"text")
        self.ssh.connect.assert_called_once()

    def test_entry_can_be_downloaded_in_a_later_session(self):
        entry = self._entry(self.manager(), "reports", "summary.txt")

        downloaded = self.manager().download_sftp_entry(entry, self.local_dir)

        self.assertEqual(downloaded[0].read_bytes(), b"sum")
        self.assertEqual(self.ssh.connect.call_count, 2)


class TestSftpClientManagerMoveFile(SftpClientManagerTestCase):
    def test_moves_into_new_sibling_dir(self):
        new_path = self.manager().move_file("/upload/a.txt", "processed")
        self.assertEqual(new_path, "/upload/processed/a.txt")
        upload_dir = self.fake_sftp.tree["upload"]
        self.assertNotIn("a.txt", upload_dir)
        self.assertEqual(upload_dir["processed"], {"a.txt": b"text"})

    def test_moves_into_existing_dir(self):
        self.manager().move_file("/upload/a.txt", "reports")
        self.assertEqual(self.fake_sftp.tree["upload"]["reports"]["a.txt"], b"text")

    def test_moves_into_absolute_dir(self):
        new_path = self.manager().move_file("/upload/b.pdf", "/upload/reports/2025")
        self.assertEqual(new_path, "/upload/reports/2025/b.pdf")
        self.assertIn("b.pdf", self.fake_sftp.tree["upload"]["reports"]["2025"])

    def test_never_overwrites_a_taken_name(self):
        manager = self.manager()
        self.fake_sftp.tree["upload"]["processed"] = {"a.txt": b"first"}
        self.assertEqual(
            manager.move_file("/upload/a.txt", "processed"),
            "/upload/processed/a_1.txt",
        )
        self.fake_sftp.tree["upload"]["a.txt"] = b"third"
        self.assertEqual(
            manager.move_file("/upload/a.txt", "processed"),
            "/upload/processed/a_2.txt",
        )
        self.assertEqual(
            self.fake_sftp.tree["upload"]["processed"],
            {"a.txt": b"first", "a_1.txt": b"text", "a_2.txt": b"third"},
        )
