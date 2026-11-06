"""The repository, commit range and files one review covers."""

from __future__ import annotations

import os
import re
import subprocess  # nosec B404 - runs git with fixed argument lists, no shell
from pathlib import Path

CORE = "montrek"
HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
EXTENSION_IMPORT = re.compile(r"^\s*(?:from|import)\s+(mt_\w+)", re.MULTILINE)
TEXT_SUFFIXES = {
    ".cfg",
    ".css",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".tex",
    ".toml",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
TEXT_NAMES = {"Dockerfile", "Makefile", ".coveragerc"}
SKIPPED_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".venv",
    "__pycache__",
    "htmlcov",
    "node_modules",
    "secrets",
    "uploads",
}
MAX_FILE_BYTES = 400_000


class ReviewScopeError(RuntimeError):
    pass


class ReviewScope:
    """What the reviewer may see.

    Every path is relative to the project root (the core checkout), so a core
    file reads ``montrek/baseclasses/...`` and an extension file
    ``montrek/mt_example/...``, in the diff as well as in the tools.

    Visible files are the git-tracked files of core (see _core_files when core
    is no checkout) and of the extensions in scope: that keeps ``.env``,
    ``secrets/``, uploads and caches out by construction. Extensions other
    than the reviewed one and those it imports stay invisible, so a core
    review never sends extension code to the model.
    """

    def __init__(
        self,
        project_root: Path,
        repo: str = CORE,
        base: str = "origin/main",
        include_worktree: bool = False,
    ) -> None:
        self.project_root = project_root.resolve()
        self.code_root = self.project_root / "montrek"
        self.repo = repo
        self.repo_dir = self._repo_dir(repo)
        self.prefix = "" if repo == CORE else f"montrek/{repo}/"
        self.base = base
        self.include_worktree = include_worktree
        self.merge_base = self.git("merge-base", base, "HEAD").strip()
        self.head = self.git("rev-parse", "--short", "HEAD").strip()
        self.commits = self.git(
            "log", "--no-color", "--format=%h %s", f"{self.merge_base}..HEAD"
        ).strip()
        self.diff = self._diff()
        self.changed_lines = self.parse_changed_lines(self.diff)
        self.extensions = self._extensions_in_scope()
        self.visible_files = self._visible_files()

    def git(self, *args: str, repo_dir: Path | None = None) -> str:
        command = ["git", "-C", str(repo_dir or self.repo_dir), *args]
        try:
            result = subprocess.run(  # noqa: S603  # nosec B603 B607 - fixed git call
                command, check=True, capture_output=True, text=True
            )
        except subprocess.CalledProcessError as error:
            raise ReviewScopeError(
                f"{' '.join(command)} failed: {error.stderr.strip()}"
            ) from error
        return result.stdout

    @property
    def changed_files(self) -> list[str]:
        return sorted(self.changed_lines)

    @staticmethod
    def parse_changed_lines(diff: str) -> dict[str, set[int]]:
        """Map each added or modified file to its added line numbers.

        Deleted files are left out; a file with only deletions maps to an empty
        set, so it still counts as changed.
        """
        changed: dict[str, set[int]] = {}
        current: set[int] | None = None
        line_number = 0
        for line in diff.splitlines():
            if line.startswith("+++ "):
                target = line[4:]
                current = None
                if target.startswith("b/"):
                    current = changed.setdefault(target[2:], set())
                continue
            if line.startswith("--- ") or line.startswith("diff --git"):
                continue
            hunk = HUNK_HEADER.match(line)
            if hunk:
                line_number = int(hunk.group(1))
                continue
            if current is None:
                continue
            if line.startswith("+"):
                current.add(line_number)
                line_number += 1
            elif line.startswith(" "):
                line_number += 1
        return changed

    @staticmethod
    def is_production_file(path: str) -> bool:
        wrapped = f"/{path}"
        return path.endswith(".py") and not any(
            part in wrapped for part in ("/tests/", "/migrations/", "/factories/")
        )

    def _repo_dir(self, repo: str) -> Path:
        if repo == CORE:
            repo_dir = self.project_root
        elif re.fullmatch(r"mt_\w+", repo):
            repo_dir = self.code_root / repo
        else:
            raise ReviewScopeError(
                f"Unknown repository '{repo}': use 'montrek' or an mt_* extension."
            )
        if not (repo_dir / ".git").exists():
            raise ReviewScopeError(f"{repo_dir} is not a git checkout.")
        return repo_dir

    def _diff(self) -> str:
        revisions = (
            [self.merge_base]
            if self.include_worktree
            else [
                self.merge_base,
                "HEAD",
            ]
        )
        prefixes = []
        if self.prefix:
            prefixes = [
                f"--src-prefix=a/{self.prefix}",
                f"--dst-prefix=b/{self.prefix}",
            ]
        return self.git(
            "diff", "--no-color", "--find-renames", "--unified=5", *prefixes, *revisions
        )

    def _extensions_in_scope(self) -> list[str]:
        if self.repo == CORE:
            return []
        extensions = {self.repo}
        for path in self.git("ls-files", "*.py").splitlines():
            source = (self.repo_dir / path).read_text(errors="replace")
            extensions.update(EXTENSION_IMPORT.findall(source))
        return sorted(
            name for name in extensions if (self.code_root / name / ".git").exists()
        )

    def _visible_files(self) -> set[str]:
        tracked = self._core_files()
        for extension in self.extensions:
            tracked += [
                f"montrek/{extension}/{path}"
                for path in self.git(
                    "ls-files", repo_dir=self.code_root / extension
                ).splitlines()
            ]
        return {path for path in tracked if self._is_readable_text(path)}

    def _core_files(self) -> list[str]:
        """Core's tracked files, or its files on disk when it is no checkout.

        CI copies core out of the app image, so there is no git repository;
        the image holds only what its .dockerignore lets through, and the
        walk skips extensions and generated directories on top of that.
        """
        if (self.project_root / ".git").exists():
            return self.git("ls-files", repo_dir=self.project_root).splitlines()
        files = []
        for directory, subdirectories, names in os.walk(self.project_root):
            subdirectories[:] = sorted(
                name
                for name in subdirectories
                if name not in SKIPPED_DIRECTORIES
                and not (Path(directory) == self.code_root and name.startswith("mt_"))
            )
            relative = Path(directory).relative_to(self.project_root)
            files += [(relative / name).as_posix() for name in names]
        return files

    def _is_readable_text(self, path: str) -> bool:
        name = path.rsplit("/", 1)[-1]
        if Path(name).suffix not in TEXT_SUFFIXES and name not in TEXT_NAMES:
            return False
        if name.startswith(".env"):
            return False
        file = self.project_root / path
        return file.is_file() and file.stat().st_size <= MAX_FILE_BYTES
