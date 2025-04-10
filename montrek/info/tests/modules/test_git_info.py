import os
import pandas as pd
import subprocess
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

        # Store current directory to restore later
        self.original_dir = os.getcwd()

    def tearDown(self):
        """Clean up after each test."""
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

        # Return to original directory
        os.chdir(self.original_dir)

    def _create_mock_git_repo(self):
        """Helper method to simulate a git repository for tests."""
        os.chdir(self.temp_dir)
        subprocess.run(["git", "init"], check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)

        # Create a dummy file and commit it
        with open(os.path.join(self.temp_dir, "test.txt"), "w") as f:
            f.write("Test content")

        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)

        # Create a tag
        subprocess.run(["git", "tag", "v1.0.0"], check=True)

        # Return to original directory
        os.chdir(self.original_dir)

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

        # Mock different return values for different commands
        def side_effect(*args, **kwargs):
            cmd = args[0]
            if "rev-parse" in cmd and "--abbrev-ref" in cmd:
                return b"master"
            elif (
                "rev-parse" in cmd
                and "--abbrev-ref" not in cmd
                and "--show-toplevel" not in cmd
            ):
                return b"abcdef1234567890"
            elif "describe" in cmd:
                return b"v1.0.0"
            elif "log" in cmd and "format:%an" in cmd[0]:
                return b"Test User"
            elif "log" in cmd and "format:%cd" in cmd[0]:
                return b"2023-01-01 12:00:00 +0000"
            elif "config" in cmd:
                return b"git@github.com:user/repo.git"
            elif "rev-parse" in cmd and "--show-toplevel" in cmd:
                return b"/path/to/repo"
            elif "rev-list" in cmd:
                return b"42"
            elif "status" in cmd:
                return b""
            else:
                return b"unknown"

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
