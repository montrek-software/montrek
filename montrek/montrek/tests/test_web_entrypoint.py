"""Tests for bin/entrypoints/web-entrypoint.sh.

The script runs in a temporary directory with a stub for `python` on PATH, so
the test sees the gunicorn command line it would start the app with.
"""

import subprocess  # nosec B404
import tempfile
from pathlib import Path

from django.test import SimpleTestCase

ENTRYPOINT = (
    Path(__file__).resolve().parents[3] / "bin" / "entrypoints" / "web-entrypoint.sh"
)
PYTHON_STUB = """#!/bin/sh
for arg in "$@"; do echo "$arg"; done
"""


class TestWebEntrypoint(SimpleTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / ".venv" / "bin").mkdir(parents=True)
        (self.root / ".venv" / "bin" / "activate").write_text("")
        (self.root / "montrek").mkdir()
        # Outside an image the script syncs the venv first.
        (self.root / "bin" / "local").mkdir(parents=True)
        sync = self.root / "bin" / "local" / "sync-python-env.sh"
        sync.write_text("#!/bin/sh\n")
        sync.chmod(0o755)
        stubs = self.root / "stubs"
        stubs.mkdir()
        (stubs / "python").write_text(PYTHON_STUB)
        (stubs / "python").chmod(0o755)
        self.path = f"{stubs}:/usr/bin:/bin"

    def gunicorn_options(self, **environment: str) -> dict[str, str]:
        result = subprocess.run(  # noqa: S603  # nosec B603
            ["/bin/bash", str(ENTRYPOINT)],
            cwd=self.root,
            env={
                "PATH": self.path,
                "APP_PORT": "8000",
                "DO_MONTREK_STARTUP_TASKS": "0",
                **environment,
            },
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        arguments = result.stdout.splitlines()
        return {
            argument.removeprefix("--"): value
            for argument, value in zip(arguments, arguments[1:], strict=False)
            if argument.startswith("--")
        }

    def test_replaces_workers_after_5000_requests_by_default(self):
        options = self.gunicorn_options()
        self.assertEqual(options["max-requests"], "5000")
        self.assertEqual(options["max-requests-jitter"], "500")

    def test_max_requests_from_environment(self):
        options = self.gunicorn_options(GUNICORN_MAX_REQUESTS="800")
        self.assertEqual(options["max-requests"], "800")
        self.assertEqual(options["max-requests-jitter"], "80")

    def test_max_requests_zero_never_replaces_workers(self):
        options = self.gunicorn_options(GUNICORN_MAX_REQUESTS="0")
        self.assertEqual(options["max-requests"], "0")
        self.assertEqual(options["max-requests-jitter"], "0")
