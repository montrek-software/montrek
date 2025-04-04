import pandas as pd
import subprocess
import os
from functools import wraps


class GitInfo:
    """
    A class to extract and process information from a git repository.
    """

    def __init__(self, git_path=None):
        """
        Initialize the GitInfo instance with a path to a git repository.

        Args:
            git_path (str, optional): Path to the git repository.
                                     If None, the current directory is used.
        """
        self.git_path = git_path if git_path else os.getcwd()
        self.is_git_repo = self._check_is_git_repo()
        self.git_info = {}

        if self.is_git_repo:
            self._collect_git_info()

    def _run_git_command(self, command_args, default="Unknown"):
        """
        Run a git command and return its output.

        Args:
            command_args (list): List of git command arguments
            default (str): Default value to return if command fails

        Returns:
            str: Command output or default value if command fails
        """
        try:
            cmd = ["git"]
            if self.git_path:
                cmd.extend(["-C", self.git_path])
            cmd.extend(command_args)

            result = subprocess.check_output(cmd).decode("utf-8").strip()
            return result
        except subprocess.CalledProcessError:
            return default

    def _check_is_git_repo(self):
        """Check if the specified path is a git repository."""
        result = self._run_git_command(["rev-parse", "--is-inside-work-tree"])

        if result == "true":
            return True
        else:
            print(
                f"Error: {self.git_path} is not a git repository or git is not installed"
            )
            return False

    def _collect_git_info(self):
        """Collect all git information and store it in self.git_info."""
        # Get current branch
        self.git_info["branch"] = self._run_git_command(
            ["rev-parse", "--abbrev-ref", "HEAD"]
        )

        # Get current commit hash
        self.git_info["commit_hash"] = self._run_git_command(["rev-parse", "HEAD"])

        # Get latest tag
        self.git_info["latest_tag"] = self._run_git_command(
            ["describe", "--tags", "--abbrev=0"], default="No tags found"
        )

        # Get commit author
        self.git_info["author"] = self._run_git_command(
            ["log", "-1", "--pretty=format:%an"]
        )

        # Get commit date
        self.git_info["commit_date"] = self._run_git_command(
            ["log", "-1", "--pretty=format:%cd", "--date=iso"]
        )

        # Get repository remote URL
        self.git_info["remote_url"] = self._run_git_command(
            ["config", "--get", "remote.origin.url"], default="No remote URL found"
        )

        # Get repo name
        repo_path = self._run_git_command(["rev-parse", "--show-toplevel"])
        self.git_info["repo_name"] = (
            os.path.basename(repo_path) if repo_path != "Unknown" else "Unknown"
        )

        # Number of commits in the current branch
        self.git_info["commit_count"] = self._run_git_command(
            ["rev-list", "--count", "HEAD"]
        )

        # Is the working directory clean?
        status = self._run_git_command(["status", "--porcelain"])
        self.git_info["is_clean"] = "True" if status == "" else "False"

    def to_dict(self):
        """Return git information as a dictionary."""
        return self.git_info.copy() if self.is_git_repo else {}

    def to_dataframe(self):
        """
        Convert git information to a pandas DataFrame.

        Returns:
            DataFrame: A pandas DataFrame containing git repository information
        """
        if not self.is_git_repo:
            return pd.DataFrame()

        return pd.DataFrame([self.git_info])
