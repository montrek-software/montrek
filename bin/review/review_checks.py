"""Deterministic checks whose results go into the review prompt.

The model is good at judging findings and poor at measuring them, so lint
results and patch coverage are computed here and handed over as facts.
"""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404 - runs ruff and the test suite, no shell
import sys
import tempfile

# The coverage XML is written by coverage.py in this run or by the user's own
# test run; it is not untrusted input.
from xml.etree import ElementTree  # nosec B405
from pathlib import Path

from review_scope import CORE, ReviewScope

OUTPUT_TAIL_LINES = 60


class ReviewChecks:
    def __init__(
        self,
        scope: ReviewScope,
        run_tests: bool = False,
        coverage_xml: Path | None = None,
    ) -> None:
        self.scope = scope
        self.run_tests = run_tests
        self.coverage_xml = coverage_xml

    def render(self) -> str:
        sections = [self.ruff()]
        if self.run_tests:
            sections.append(self.tests_with_coverage())
        elif self.coverage_xml:
            sections.append(self.patch_coverage(self.coverage_xml))
        else:
            sections.append(
                "### Patch coverage\nNot measured in this run. Judge test coverage "
                "by reading the tests of the changed code."
            )
        return "\n\n".join(sections)

    def ruff(self) -> str:
        files = [
            path
            for path in self.scope.changed_files
            if path.endswith(".py") and (self.scope.project_root / path).is_file()
        ]
        if not files:
            return "### ruff\nNo Python files changed."
        ruff = shutil.which("ruff")
        if ruff is None:
            return "### ruff\nNot installed; skipped."
        result = subprocess.run(  # noqa: S603  # nosec B603 - paths from git
            [ruff, "check", "--no-fix", "--output-format=concise", *files],
            cwd=self.scope.project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        output = result.stdout.strip() or "Clean."
        return f"### ruff (changed files)\n```\n{output}\n```"

    def test_labels(self) -> list[str]:
        if self.scope.repo != CORE:
            return [self.scope.repo]
        labels = set()
        for path in self.scope.changed_files:
            parts = path.split("/")
            if len(parts) > 2 and parts[0] == "montrek":
                app_dir = self.scope.code_root / parts[1]
                if (app_dir / "apps.py").is_file():
                    labels.add(parts[1])
        return sorted(labels)

    def tests_with_coverage(self) -> str:
        labels = self.test_labels()
        if not labels:
            return "### Tests\nNo Django app touched; no tests run."
        with tempfile.TemporaryDirectory(prefix="ai-review-") as tmp:
            # A private data file, so the developer's own .coverage stays as is.
            env = {**os.environ, "COVERAGE_FILE": str(Path(tmp) / ".coverage")}
            xml_path = Path(tmp) / "coverage.xml"
            coverage = [sys.executable, "-m", "coverage"]
            test_run = self._run(
                [
                    *coverage,
                    "run",
                    "--rcfile=.coveragerc",
                    "manage.py",
                    "test",
                    "--noinput",
                    *labels,
                ],
                env,
            )
            self._run([*coverage, "combine"], env)
            self._run([*coverage, "xml", "-o", str(xml_path)], env)
            status = "passed" if test_run.returncode == 0 else "FAILED"
            tail = "\n".join(
                (test_run.stdout + test_run.stderr)
                .strip()
                .splitlines()[-OUTPUT_TAIL_LINES:]
            )
            report = (
                f"### Tests: {status} (`manage.py test {' '.join(labels)}`)\n"
                f"```\n{tail}\n```"
            )
            if xml_path.is_file():
                report += "\n\n" + self.patch_coverage(xml_path)
            return report

    def patch_coverage(self, xml_path: Path) -> str:
        covered_total, measurable_total, rows = self.patch_coverage_figures(xml_path)
        if not measurable_total:
            return "### Patch coverage\nNo measurable changed production lines."
        percent = 100 * covered_total / measurable_total
        details = "\n".join(rows) or "All changed production lines are covered."
        return (
            f"### Patch coverage: {percent:.0f}% "
            f"({covered_total}/{measurable_total} changed lines)\n{details}"
        )

    def patch_coverage_figures(self, xml_path: Path) -> tuple[int, int, list[str]]:
        """Covered and measurable changed production lines, and one row per
        file with uncovered lines."""
        measured = self._coverage_lines(xml_path)
        rows = []
        covered_total = measurable_total = 0
        for path in self.scope.changed_files:
            if not self.scope.is_production_file(path):
                continue
            changed = self.scope.changed_lines[path]
            if not changed:
                continue
            hits = measured.get(path)
            if hits is None:
                rows.append(f"- `{path}`: not in the coverage data (never imported?)")
                measurable_total += len(changed)
                continue
            measurable = sorted(line for line in changed if line in hits)
            uncovered = [line for line in measurable if hits[line] == 0]
            measurable_total += len(measurable)
            covered_total += len(measurable) - len(uncovered)
            if uncovered:
                rows.append(
                    f"- `{path}`: uncovered changed lines {self._ranges(uncovered)}"
                )
        return covered_total, measurable_total, rows

    def _coverage_lines(self, xml_path: Path) -> dict[str, dict[int, int]]:
        """Line hits per changed file, keyed by its project-relative path.

        Coverage names files relative to wherever it ran: the Django root
        (``mt_example/...``, also CI's form), the extension itself, or
        absolute. Each changed file is looked up under all of these names.
        """
        tree = ElementTree.parse(xml_path)  # noqa: S314  # nosec B314 - see import
        names = self._coverage_names()
        lines: dict[str, dict[int, int]] = {}
        for cls in tree.getroot().iter("class"):
            filename = cls.get("filename", "").replace("\\", "/")
            path = names.get(filename) or next(
                (p for p in self.scope.changed_files if filename.endswith(f"/{p}")),
                None,
            )
            if path is not None:
                lines[path] = {
                    int(line.get("number", 0)): int(line.get("hits", 0))
                    for line in cls.iter("line")
                }
        return lines

    def _coverage_names(self) -> dict[str, str]:
        """Every name a coverage report may use for a changed file."""
        names: dict[str, str] = {}
        prefixes = ["", "montrek/"]
        if self.scope.prefix:
            prefixes.append(self.scope.prefix)
        for path in self.scope.changed_files:
            for prefix in prefixes:
                if path.startswith(prefix):
                    names.setdefault(path.removeprefix(prefix), path)
        return names

    def _run(
        self, command: list[str], env: dict[str, str]
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(  # noqa: S603  # nosec B603 - fixed command
            command,
            cwd=self.scope.code_root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    @staticmethod
    def _ranges(numbers: list[int]) -> str:
        ranges: list[str] = []
        start = previous = numbers[0]
        for number in [*numbers[1:], None]:
            if number is not None and number == previous + 1:
                previous = number
                continue
            ranges.append(str(start) if start == previous else f"{start}-{previous}")
            if number is not None:
                start = previous = number
        return ", ".join(ranges)
