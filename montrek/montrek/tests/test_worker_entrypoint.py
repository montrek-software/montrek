"""Tests for bin/entrypoints/worker-entrypoint.sh.

The script runs in a temporary directory with stubs for `python` and `nproc` on
PATH, so the test sees the Celery command line and environment it would start
the worker with.
"""

import subprocess  # nosec B404
import tempfile
from pathlib import Path

from django.test import SimpleTestCase

ENTRYPOINT = (
    Path(__file__).resolve().parents[3] / "bin" / "entrypoints" / "worker-entrypoint.sh"
)
PYTHON_STUB = """#!/bin/sh
echo "REMAP_SIGTERM=$REMAP_SIGTERM"
for arg in "$@"; do echo "$arg"; done
"""
NPROC_STUB = "#!/bin/sh\necho 2\n"


class TestWorkerEntrypoint(SimpleTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / ".venv" / "bin").mkdir(parents=True)
        (self.root / ".venv" / "bin" / "activate").write_text("")
        (self.root / "montrek").mkdir()
        stubs = self.root / "stubs"
        stubs.mkdir()
        for name, content in (("python", PYTHON_STUB), ("nproc", NPROC_STUB)):
            (stubs / name).write_text(content)
            (stubs / name).chmod(0o755)
        self.path = f"{stubs}:/usr/bin:/bin"

    def run_entrypoint(self, **environment: str) -> subprocess.CompletedProcess:
        return subprocess.run(  # noqa: S603  # nosec B603
            ["/bin/bash", str(ENTRYPOINT)],
            cwd=self.root,
            env={"PATH": self.path, **environment},
            capture_output=True,
            text=True,
            check=False,
        )

    def worker_command(self, **environment: str) -> tuple[dict[str, str], str]:
        result = self.run_entrypoint(**environment)
        self.assertEqual(result.returncode, 0, result.stderr)
        remap, *arguments = result.stdout.splitlines()
        options = dict(
            argument.removeprefix("--").split("=", 1)
            for argument in arguments
            if argument.startswith("--") and "=" in argument
        )
        options["queue"] = arguments[arguments.index("-Q") + 1]
        return options, remap.removeprefix("REMAP_SIGTERM=")

    def test_sequential_worker_runs_one_task_at_a_time(self):
        options, _ = self.worker_command(SERVICE="sequential_worker")
        self.assertEqual(options["concurrency"], "1")
        self.assertEqual(options["queue"], "sequential_queue")
        self.assertEqual(options["pool"], "prefork")

    def test_sequential_worker_ignores_worker_concurrency(self):
        result = self.run_entrypoint(
            SERVICE="sequential_worker", WORKER_CONCURRENCY="4"
        )
        self.assertIn("--concurrency=1", result.stdout)
        self.assertIn("ignoring WORKER_CONCURRENCY=4", result.stderr)

    def test_parallel_worker_concurrency(self):
        for environment, expected in (
            ({}, "4"),
            ({"WORKER_CONCURRENCY": "6"}, "6"),
            ({"SET_CONCURRENCY": "3"}, "3"),
            ({"WORKER_CONCURRENCY": "6", "SET_CONCURRENCY": "3"}, "6"),
            ({"WORKER_CONCURRENCY": "", "SET_CONCURRENCY": "3"}, "3"),
        ):
            with self.subTest(environment=environment):
                options, _ = self.worker_command(
                    SERVICE="parallel_worker", **environment
                )
                self.assertEqual(options["concurrency"], expected)
                self.assertEqual(options["queue"], "parallel_queue")

    def test_fast_worker_concurrency(self):
        for environment, expected in (
            ({}, "100"),  # 50 per CPU, with nproc stubbed to 2
            ({"WORKER_CONCURRENCY": "20"}, "20"),
            ({"WORKER_CONCURRENCY": "800"}, "500"),
        ):
            with self.subTest(environment=environment):
                options, _ = self.worker_command(SERVICE="fast_worker", **environment)
                self.assertEqual(options["concurrency"], expected)
                self.assertEqual(options["pool"], "gevent")
                self.assertEqual(options["queue"], "fast_queue")

    def test_queue_and_pool_can_be_set(self):
        options, _ = self.worker_command(
            SERVICE="parallel_worker", QUEUE="other_queue", POOL="solo"
        )
        self.assertEqual(options["queue"], "other_queue")
        self.assertEqual(options["pool"], "solo")

    def test_prefork_workers_return_tasks_to_the_queue_on_sigterm(self):
        for service in ("sequential_worker", "parallel_worker"):
            with self.subTest(service=service):
                _, remap = self.worker_command(SERVICE=service)
                self.assertEqual(remap, "SIGQUIT")

    def test_gevent_worker_keeps_the_warm_shutdown(self):
        # Celery's soft and cold shutdown fail under gevent and lose the task.
        _, remap = self.worker_command(SERVICE="fast_worker")
        self.assertEqual(remap, "")

    def test_invalid_concurrency_stops_the_start(self):
        for value in ("abc", "0", "-2"):
            with self.subTest(value=value):
                result = self.run_entrypoint(
                    SERVICE="parallel_worker", WORKER_CONCURRENCY=value
                )
                self.assertEqual(result.returncode, 1)
                self.assertIn("must be a positive number", result.stderr)
                self.assertEqual(result.stdout, "")

    def test_unknown_service_stops_the_start(self):
        result = self.run_entrypoint(SERVICE="other_worker")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Unknown service other_worker", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_celery_replaces_the_shell(self):
        # PID 1 of the container ignores SIGTERM unless it handles it, so the
        # shell must not stay in between: Celery takes over the shell's PID.
        stub = self.root / "stubs" / "python"
        stub.write_text('#!/bin/sh\necho "$$"\n')
        result = subprocess.run(  # noqa: S603  # nosec B603
            ["/bin/bash", "-c", f'echo "$$"; exec /bin/bash {ENTRYPOINT}'],
            cwd=self.root,
            env={"PATH": self.path, "SERVICE": "fast_worker"},
            capture_output=True,
            text=True,
            check=False,
        )
        shell_pid, celery_pid = result.stdout.split()
        self.assertEqual(celery_pid, shell_pid)
