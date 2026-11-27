import os
import pandas as pd
import subprocess  # nosec B404 - builds a git repository for the tests
import tempfile
import shutil
from unittest.mock import patch

from django.test import TestCase

from info.modules.git_info import GitInfo


class GitInfoTests(TestCase):
    """Test suite for the GitInfo class."""

    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary directory that will simulate a git repository
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up after each test."""
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _git(self, *args: str) -> None:
        # Fixed git command in a temporary directory.
        subprocess.run(  # noqa: S603  # nosec B603 B607
            ["git", "-C", self.temp_dir, *args],  # noqa: S607
            check=True,
            capture_output=True,
        )

    def _create_mock_git_repo(self):
        """Helper method to simulate a git repository for tests."""
        self._git("init")
        self._git("config", "user.name", "Test User")
        self._git("config", "user.email", "test@example.com")

        # Create a dummy file and commit it
        with open(os.path.join(self.temp_dir, "test.txt"), "w") as f:
            f.write("Test content")

        self._git("add", ".")
        self._git("commit", "-m", "Initial commit")
        self._git("tag", "v1.0.0")

    def test_init_with_valid_git_repo(self):
        """Test initializing GitInfo with a valid git repository."""
        self._create_mock_git_repo()

        git_info = GitInfo(self.temp_dir)

        self.assertTrue(git_info.is_git_repo)
        self.assertEqual(git_info.git_path, self.temp_dir)
        self.assertIsNotNone(git_info.git_info)
        self.assertIn("branch", git_info.git_info)

    def test_init_with_invalid_path(self):
        """Test initializing GitInfo with a non-existent path."""
        non_existent_path = "/path/does/not/exist"

        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.side_effect = subprocess.CalledProcessError(1, "git")
            git_info = GitInfo(non_existent_path)

            self.assertFalse(git_info.is_git_repo)
            self.assertEqual(git_info.git_path, non_existent_path)
            self.assertEqual(git_info.git_info, {})

    def test_init_with_non_git_repo(self):
        """Test initializing GitInfo with a path that is not a git repository."""
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.side_effect = subprocess.CalledProcessError(128, "git")
            git_info = GitInfo(self.temp_dir)

            self.assertFalse(git_info.is_git_repo)
            self.assertEqual(git_info.git_info, {})

    def test_init_without_git_executable(self):
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.side_effect = FileNotFoundError(2, "No such file", "git")
            with self.assertLogs("info.modules.git_info", "WARNING") as logs:
                git_info = GitInfo(self.temp_dir)

        self.assertFalse(git_info.is_git_repo)
        self.assertEqual(git_info.to_dict(), {})
        self.assertTrue(git_info.to_dataframe().empty)
        self.assertIn("git is not installed", logs.output[0])

    @patch("subprocess.check_output")
    def test_run_git_command_success(self, mock_check_output):
        """Test the _run_git_command method with successful command execution."""
        # Set up a constant return value instead of a sequence
        mock_check_output.return_value = b"test-branch"

        # Create a mock GitInfo object without calling __init__
        # to avoid the automatic call to _check_is_git_repo
        git_info = GitInfo.__new__(GitInfo)
        git_info.git_path = "/fake/path"

        # Directly test the _run_git_command method
        result = git_info._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])

        self.assertEqual(result, "test-branch")
        mock_check_output.assert_called_once()

    @patch("subprocess.check_output")
    def test_run_git_command_failure(self, mock_check_output):
        """Test the _run_git_command method with failed command execution."""
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "git")

        git_info = GitInfo("/fake/path")
        # Access the protected method for testing
        result = git_info._run_git_command(
            ["rev-parse", "--abbrev-ref", "HEAD"], default="custom-default"
        )

        self.assertEqual(result, "custom-default")

    @patch("subprocess.check_output")
    def test_collect_git_info(self, mock_check_output):
        """Test the _collect_git_info method."""

        # Output per command, by the first argument found in it; the order
        # matters, as "--abbrev-ref" commands are "rev-parse" commands too.
        outputs = {
            "--abbrev-ref": b"master",
            "rev-parse": b"abcdef1234567890",
            "describe": b"v1.0.0",
            "--pretty=format:%an": b"Test User",
            "--pretty=format:%cd": b"2023-01-01 12:00:00 +0000",
            "config": b"git@github.com:user/repo.git",
            "rev-list": b"42",
            "status": b"",
        }

        def side_effect(cmd, *args, **kwargs):
            return next(
                (output for arg, output in outputs.items() if arg in cmd), b"unknown"
            )

        mock_check_output.side_effect = side_effect

        git_info = GitInfo("/fake/path")
        git_info.is_git_repo = True
        git_info._collect_git_info()

        # Verify all expected keys are present
        expected_keys = [
            "branch",
            "commit_hash",
            "latest_tag",
            "author",
            "commit_date",
            "remote_url",
            "repo_name",
            "commit_count",
            "is_clean",
        ]
        for key in expected_keys:
            self.assertIn(key, git_info.git_info)

        # Verify specific values
        self.assertEqual(git_info.git_info["branch"], "master")
        self.assertEqual(git_info.git_info["commit_hash"], "abcdef1234567890")
        self.assertEqual(git_info.git_info["latest_tag"], "v1.0.0")
        self.assertEqual(git_info.git_info["is_clean"], "True")
        self.assertEqual(git_info.git_info["commit_count"], "42")
        self.assertEqual(git_info.git_info["author"], "Test User")

    def test_to_dict_with_valid_repo(self):
        """Test the to_dict method with a valid git repository."""
        self._create_mock_git_repo()

        git_info = GitInfo(self.temp_dir)
        git_dict = git_info.to_dict()

        self.assertIsInstance(git_dict, dict)
        self.assertIn("branch", git_dict)
        self.assertIn("commit_hash", git_dict)

    def test_to_dict_with_invalid_repo(self):
        """Test the to_dict method with an invalid git repository."""
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.side_effect = subprocess.CalledProcessError(128, "git")
            git_info = GitInfo(self.temp_dir)
            git_dict = git_info.to_dict()

            self.assertEqual(git_dict, {})

    def test_to_dataframe_with_valid_repo(self):
        """Test the to_dataframe method with a valid git repository."""
        self._create_mock_git_repo()

        git_info = GitInfo(self.temp_dir)
        df = git_info.to_dataframe()

        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 1)  # Should have one row
        self.assertIn("branch", df.columns)

    def test_to_dataframe_with_invalid_repo(self):
        """Test the to_dataframe method with an invalid git repository."""
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.side_effect = subprocess.CalledProcessError(128, "git")
            git_info = GitInfo(self.temp_dir)
            df = git_info.to_dataframe()

            self.assertIsInstance(df, pd.DataFrame)
            self.assertTrue(df.empty)

    def test_integration_in_django_view(self):
        """Test integrating GitInfo in a Django view context."""
        # This test simulates how GitInfo might be used in a Django view
        from django.http import HttpResponse
        from django.test import RequestFactory

        self._create_mock_git_repo()

        def sample_view(request):
            git_info = GitInfo(self.temp_dir)
            df = git_info.to_dataframe()
            if not df.empty:
                # Convert DataFrame to HTML for the response
                html = df.to_html()
                return HttpResponse(html)
            return HttpResponse("No git info available")

        # Create a fake request
        factory = RequestFactory()
        request = factory.get("/")

        # Call the view
        response = sample_view(request)

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"<table", response.content)
        self.assertIn(b"branch", response.content)
