"""Check a branch against the mechanical criteria of CONTRIBUTION_CRITERIA.md.

Prints a Markdown report: one row per criterion with ✅ passed, ❌ failed,
⚠️ needs a look, or ℹ️ for what needs a human or could not be measured.
Report only, unless --enforce: then a failed M criterion exits with 1.

Run it through ``make contribution-check`` locally, or in CI after the tests;
``--help`` lists the options.
"""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 - runs pre-commit and manage.py, no shell
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from review_checks import ReviewChecks
from review_scope import CORE, ReviewScope, ReviewScopeError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PASS, FAIL, WARN, INFO = "✅", "❌", "⚠️", "ℹ️"
MAX_LOC = 400
MAX_LOC_WITH_AGREEMENT = 800
MIN_PATCH_COVERAGE = 85.0
OUTPUT_LINES = 200
MAX_LISTED = 10

LOC_SUFFIXES = {".py", ".html", ".js", ".css"}
LOC_EXCLUDED_PARTS = ("tests", "migrations", "factories", "static", "node_modules")
FRAMEWORK_CORE = (
    "montrek/baseclasses/",
    "montrek/middleware/",
    "montrek/testing/",
    "montrek/montrek/settings.py",
    "montrek/montrek/urls.py",
    "montrek/montrek/celery.py",
)
LINTER_CONFIGS = {
    "pyproject.toml",
    ".pre-commit-config.yaml",
    ".coveragerc",
    "setup.cfg",
}
DEPENDENCY_FILES = {"requirements.in", "requirements.txt", "uv.lock"}

ISSUE_IN_TITLE = re.compile(r"#\d+|^\s*\d+[-_ ]|\b[A-Z][A-Z0-9]+-\d+\b")
ISSUE_BRANCH = re.compile(r"^\d+[-_]")
BAD_COMMIT_SUBJECT = re.compile(
    r"^(wip|fix|fixes|asdf|tmp|test|update|changes?|\.+)$", re.IGNORECASE
)
TEST_DEFINITION = re.compile(r"^\s*def (test_\w+)")
SKIPPED_TEST = re.compile(
    r"@(?:unittest\.)?(?:skip\w*|expectedFailure)\b|tag\(\s*['\"]functional"
)
SUPPRESSION = re.compile(
    r"#\s*noqa(?::\s*[A-Z]+\d+(?:\s*,\s*[A-Z]+\d+)*)?"
    r"|#\s*type:\s*ignore(?:\[[^\]]*\])?"
    r"|#\s*nosec(?:\s+B\d+)*"
    r"|djlint:off"
)
BLANKET_NOQA = re.compile(r"#\s*noqa(?!\s*:)")
RAW_SQL = re.compile(
    r"\.raw\(|\.extra\(|RawSQL\(|connection\.cursor\(|cursor\.execute\("
)
UNSAFE = re.compile(
    r"mark_safe\(|\|\s*safe\b|autoescape\s+off|\beval\(|\bexec\(|pickle\.loads\("
    r"|shell\s*=\s*True"
)
DESTRUCTIVE_MIGRATION = re.compile(r"\b(RemoveField|DeleteModel)\(")
RISKY_MIGRATION = re.compile(
    r"\b(AlterField|RenameField|RenameModel|RemoveConstraint|RemoveIndex)\("
)
IRREVERSIBLE_RUN_PYTHON = re.compile(r"RunPython\(\s*[\w.]+\s*\)")
SCHEMA_OPERATION = re.compile(
    r"\b(CreateModel|AddField|AlterField|RemoveField|DeleteModel|RenameField"
    r"|AddIndex|AddConstraint|AlterUniqueTogether)\("
)
DESCRIPTION_SECTIONS = {
    "what changed": re.compile(r"what\b.*chang|\bsummary\b", re.IGNORECASE),
    "why": re.compile(r"\bwhy\b", re.IGNORECASE),
    "how it was tested": re.compile(r"test(ed|\s*plan)", re.IGNORECASE),
    "deliberately not done": re.compile(r"not\s+done|out of scope", re.IGNORECASE),
    "risks": re.compile(r"\brisks?\b", re.IGNORECASE),
}


@dataclass
class CriterionResult:
    criterion: str
    title: str
    status: str
    detail: str = ""


class ContributionCheck:
    def __init__(self, options: argparse.Namespace) -> None:
        self.options = options
        self.scope = ReviewScope(
            PROJECT_ROOT,
            repo=options.repo,
            base=options.base,
            include_worktree=options.worktree,
        )
        self.statuses = self.scope.file_statuses()
        self.added: dict[str, list[tuple[int, str]]] = {}
        self.removed: dict[str, list[str]] = {}
        for path, sign, number, text in self.diff_lines(self.scope.diff):
            if sign == "+":
                self.added.setdefault(path, []).append((number, text))
            else:
                self.removed.setdefault(path, []).append(text)
        self.body = options.body_file.read_text() if options.body_file else options.body
        self.outputs: dict[str, str] = {}

    @classmethod
    def main(cls, argv: list[str] | None = None) -> int:
        options = cls.parse_arguments(argv)
        try:
            check = cls(options)
        except ReviewScopeError as error:
            print(f"Error: {error}", file=sys.stderr)
            return 2
        results = check.run()
        report = check.render(results)
        if options.output:
            options.output.write_text(report)
        else:
            print(report)
        failed = [
            r for r in results if r.status == FAIL and r.criterion.startswith("M")
        ]
        return 1 if options.enforce and failed else 0

    @staticmethod
    def parse_arguments(argv: list[str] | None) -> argparse.Namespace:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--repo", default=CORE)
        parser.add_argument("--base", default="origin/main")
        parser.add_argument("--worktree", action="store_true")
        parser.add_argument("--coverage-xml", type=Path)
        parser.add_argument(
            "--tests-outcome", default="", help="success, failure, ... of the tests"
        )
        parser.add_argument("--title", default="", help="pull request title")
        parser.add_argument("--body", default="", help="pull request description")
        parser.add_argument("--body-file", type=Path)
        parser.add_argument("--branch", default="", help="pull request branch")
        parser.add_argument("--draft", default="", help="'true' for a draft")
        parser.add_argument("--skip-pre-commit", action="store_true")
        parser.add_argument("--skip-migrations", action="store_true")
        parser.add_argument("--output", type=Path)
        parser.add_argument(
            "--enforce", action="store_true", help="exit 1 on a failed M criterion"
        )
        return parser.parse_args(argv)

    def run(self) -> list[CriterionResult]:
        return [
            self.issue_in_title(),
            self.effective_loc(),
            self.framework_core(),
            CriterionResult("M4", "No unrelated changes", INFO, "Needs a human."),
            self.tests_green(),
            self.patch_coverage(),
            CriterionResult(
                "M7", "Total coverage not lower than main", INFO, "Not measured."
            ),
            self.tests_kept(),
            self.components_tested(),
            self.pre_commit(),
            self.pre_commit_all_files(),
            self.suppressions(),
            self.linter_configs(),
            self.mypy(),
            CriterionResult(
                "M14", "SonarQube quality gate", INFO, "See the SonarQube comment."
            ),
            self.pattern_check(
                "M16", "No raw SQL", RAW_SQL, "Raw SQL or a cursor; use the ORM."
            ),
            self.pattern_check(
                "M17",
                "No unsafe constructs on user input",
                UNSAFE,
                "Check that no user input reaches these.",
            ),
            CriterionResult(
                "M18", "Views enforce authorisation", INFO, "Needs a human."
            ),
            self.dependencies(),
            self.missing_migrations(),
            self.migrations_safe(),
            self.migrations_count(),
            self.migrations_separated(),
            self.query_count_tests(),
            self.branch_name(),
            self.no_merge_commits(),
            self.commit_messages(),
            self.description(),
            self.not_draft(),
        ]

    # Scope and size

    def issue_in_title(self) -> CriterionResult:
        title = self.options.title
        if not title:
            return CriterionResult("M1", "Issue in the title", INFO, "No title given.")
        if ISSUE_IN_TITLE.search(title):
            return CriterionResult("M1", "Issue in the title", PASS)
        return CriterionResult(
            "M1", "Issue in the title", FAIL, "No issue ID like `#123` in the title."
        )

    def effective_loc(self) -> CriterionResult:
        total = sum(
            self.count_effective_lines(path, [text for _, text in lines])
            for path, lines in self.added.items()
            if self.counts_for_loc(path)
        )
        if total <= MAX_LOC:
            status = PASS
        elif total <= MAX_LOC_WITH_AGREEMENT:
            status = WARN
        else:
            status = FAIL
        note = {
            PASS: "",
            WARN: " Needs prior written agreement.",
            FAIL: " Split it.",
        }[status]
        return CriterionResult(
            "M2",
            f"At most {MAX_LOC} effective LOC",
            status,
            f"{total} added or modified production lines.{note}",
        )

    def framework_core(self) -> CriterionResult:
        title = "No framework-core files"
        if self.scope.repo != CORE:
            return CriterionResult("M3", title, PASS, "Extension: no core files.")
        touched = [p for p in self.statuses if p.startswith(FRAMEWORK_CORE)]
        if not touched:
            return CriterionResult("M3", title, PASS)
        return CriterionResult(
            "M3", title, FAIL, "Needs agreement: " + self.listing(touched)
        )

    # Build, test, coverage

    def tests_green(self) -> CriterionResult:
        outcome = self.options.tests_outcome
        if outcome == "success":
            return CriterionResult("M5", "Tests green", PASS)
        if outcome in {"failure", "cancelled"}:
            return CriterionResult("M5", "Tests green", FAIL, f"Tests: {outcome}.")
        return CriterionResult("M5", "Tests green", INFO, "Test result not given.")

    def patch_coverage(self) -> CriterionResult:
        title = f"Patch coverage ≥ {MIN_PATCH_COVERAGE:.0f} %"
        xml = self.options.coverage_xml
        if not xml or not xml.is_file():
            return CriterionResult("M6", title, INFO, "No coverage report.")
        covered, measurable, rows = ReviewChecks(self.scope).patch_coverage_figures(xml)
        if not measurable:
            return CriterionResult(
                "M6", title, PASS, "No measurable changed production lines."
            )
        percent = 100 * covered / measurable
        detail = f"{percent:.0f} % ({covered}/{measurable} changed lines)."
        if rows:
            detail += " " + " ".join(
                row.removeprefix("- ") for row in rows[:MAX_LISTED]
            )
        status = PASS if percent >= MIN_PATCH_COVERAGE else FAIL
        return CriterionResult("M6", title, status, detail)

    def tests_kept(self) -> CriterionResult:
        title = "No test deleted or skipped"
        removed = {
            match.group(1)
            for path, lines in self.removed.items()
            for text in lines
            if (match := TEST_DEFINITION.match(text))
        }
        re_added = {
            match.group(1)
            for path, lines in self.added.items()
            for _, text in lines
            if (match := TEST_DEFINITION.match(text))
        }
        problems = [f"`{name}` removed" for name in sorted(removed - re_added)]
        problems += [
            f"`{path}:{number}` skips a test"
            for path, number, _ in self.added_matching(SKIPPED_TEST, tests=True)
        ]
        if not problems:
            return CriterionResult("M8", title, PASS)
        return CriterionResult(
            "M8", title, FAIL, "Justify in the description: " + self.listing(problems)
        )

    def components_tested(self) -> CriterionResult:
        title = "Changed views, managers, repositories are tested"
        untested = []
        changed_tests = {self.app_of(p) for p in self.statuses if self.is_test(p)}
        for path in self.added:
            if self.is_component(path) and self.app_of(path) not in changed_tests:
                untested.append(path)
        if not untested:
            return CriterionResult("M9", title, PASS)
        return CriterionResult(
            "M9",
            title,
            WARN,
            "No test changed in the same app for: " + self.listing(untested),
        )

    # Static analysis

    def pre_commit(self) -> CriterionResult:
        """pre-commit on the files the change touches: what it is answerable
        for. Hooks that fix files (ruff --fix, black) change them in place."""
        title = "pre-commit clean on the changed files"
        if reason := self.pre_commit_unavailable():
            return CriterionResult("M10", title, INFO, reason)
        files = [
            path.removeprefix(self.scope.prefix)
            for path in self.scope.changed_files
            if (self.scope.project_root / path).is_file()
        ]
        if not files:
            return CriterionResult("M10", title, PASS, "No file to check.")
        status, detail = self.run_pre_commit(["--files", *files], "pre-commit")
        return CriterionResult("M10", title, status, detail)

    def pre_commit_all_files(self) -> CriterionResult:
        """The catalogue's --all-files run, for information: in a repository
        that was never clean as a whole it fails for code no change touched.
        Runs after the changed-files check, whose fixes it may then see."""
        title = "pre-commit --all-files (whole repository)"
        if reason := self.pre_commit_unavailable():
            return CriterionResult("M10", title, INFO, reason)
        status, detail = self.run_pre_commit(["--all-files"], "pre-commit --all-files")
        if status == FAIL:
            detail += " Includes code this change does not touch."
        return CriterionResult("M10", title, INFO if status == FAIL else PASS, detail)

    def pre_commit_unavailable(self) -> str:
        if self.options.skip_pre_commit:
            return "Skipped."
        if not (self.scope.repo_dir / ".pre-commit-config.yaml").is_file():
            return "No .pre-commit-config.yaml."
        return ""

    def run_pre_commit(self, arguments: list[str], name: str) -> tuple[str, str]:
        result = self.execute(
            [sys.executable, "-m", "pre_commit", "run", "--color", "never", *arguments],
            self.scope.repo_dir,
        )
        self.outputs[name] = result.stdout + result.stderr
        if result.returncode == 0:
            return PASS, ""
        failed = re.findall(r"^(.+?)\.{3,}Failed$", self.outputs[name], re.M)
        return FAIL, ("Failed: " + ", ".join(failed)) if failed else "Failed."

    def suppressions(self) -> CriterionResult:
        title = "Suppressions have a reason"
        blanket, unexplained = [], []
        for path, lines in self.added.items():
            for number, text in lines:
                if not SUPPRESSION.search(text):
                    continue
                location = f"`{path}:{number}`"
                if BLANKET_NOQA.search(text):
                    blanket.append(location)
                elif not self.has_reason(text):
                    unexplained.append(location)
        if blanket:
            return CriterionResult(
                "M11", title, FAIL, "Blanket `# noqa`: " + self.listing(blanket)
            )
        if unexplained:
            return CriterionResult(
                "M11", title, WARN, "No reason given: " + self.listing(unexplained)
            )
        return CriterionResult("M11", title, PASS)

    def linter_configs(self) -> CriterionResult:
        title = "Linter configuration not weakened"
        changed = [p for p in self.statuses if Path(p).name in LINTER_CONFIGS]
        if not changed:
            return CriterionResult("M12", title, PASS)
        return CriterionResult(
            "M12", title, WARN, "Changed, check it: " + self.listing(changed)
        )

    def mypy(self) -> CriterionResult:
        title = "mypy clean"
        config = self.scope.repo_dir / ".pre-commit-config.yaml"
        if config.is_file() and "mypy" in config.read_text():
            return CriterionResult("M13", title, INFO, "Runs as part of M10.")
        return CriterionResult("M13", title, INFO, "No mypy hook configured.")

    def pattern_check(
        self, criterion: str, title: str, pattern: re.Pattern[str], advice: str
    ) -> CriterionResult:
        found = [
            f"`{path}:{number}`"
            for path, number, _ in self.added_matching(pattern, tests=False)
        ]
        if not found:
            return CriterionResult(criterion, title, PASS)
        return CriterionResult(
            criterion, title, WARN, f"{advice} {self.listing(found)}"
        )

    def dependencies(self) -> CriterionResult:
        title = "New dependencies documented"
        changed = [p for p in self.statuses if Path(p).name in DEPENDENCY_FILES]
        if not changed:
            return CriterionResult("M19", title, PASS, "No dependency file changed.")
        return CriterionResult(
            "M19",
            title,
            WARN,
            "List purpose, licence and maintenance in the description: "
            + self.listing(changed),
        )

    # Migrations

    def missing_migrations(self) -> CriterionResult:
        title = "No missing migrations"
        if self.options.skip_migrations:
            return CriterionResult("M20", title, INFO, "Skipped.")
        result = self.execute(
            [sys.executable, "manage.py", "makemigrations", "--check", "--dry-run"],
            self.scope.code_root,
        )
        if result.returncode == 0:
            return CriterionResult("M20", title, PASS)
        # Only shown when it failed: a clean run is just system-check noise.
        self.outputs["makemigrations --check --dry-run"] = result.stdout + result.stderr
        if result.returncode == 1:
            return CriterionResult(
                "M20", title, FAIL, "Missing migrations, see output."
            )
        return CriterionResult("M20", title, WARN, "Could not run, see output.")

    def migrations_safe(self) -> CriterionResult:
        title = "Migrations additive and reversible"
        destructive, risky, irreversible = [], [], []
        for path in self.new_migrations():
            source = (self.scope.project_root / path).read_text(errors="replace")
            if DESTRUCTIVE_MIGRATION.search(source):
                destructive.append(path)
            elif RISKY_MIGRATION.search(source):
                risky.append(path)
            if IRREVERSIBLE_RUN_PYTHON.search(source):
                irreversible.append(path)
        if destructive or irreversible:
            parts = []
            if destructive:
                parts.append("destructive: " + self.listing(destructive))
            if irreversible:
                parts.append("RunPython without reverse: " + self.listing(irreversible))
            return CriterionResult("M21", title, FAIL, "; ".join(parts) + ".")
        if risky:
            return CriterionResult(
                "M21", title, WARN, "Check for narrowing: " + self.listing(risky)
            )
        return CriterionResult("M21", title, PASS)

    def migrations_count(self) -> CriterionResult:
        title = "One migration per app, merged ones untouched"
        edited = [
            p for p, s in self.statuses.items() if self.is_migration(p) and s != "A"
        ]
        per_app: dict[str, list[str]] = {}
        for path in self.new_migrations():
            per_app.setdefault(str(Path(path).parent.parent), []).append(path)
        several = [app for app, paths in per_app.items() if len(paths) > 1]
        problems = []
        if edited:
            problems.append("edited or removed: " + self.listing(edited))
        if several:
            problems.append("more than one in: " + self.listing(several))
        if problems:
            return CriterionResult("M22", title, FAIL, "; ".join(problems) + ".")
        return CriterionResult("M22", title, PASS)

    def migrations_separated(self) -> CriterionResult:
        title = "Data and schema migrations separated"
        mixed = []
        for path in self.new_migrations():
            source = (self.scope.project_root / path).read_text(errors="replace")
            if "RunPython(" in source and SCHEMA_OPERATION.search(source):
                mixed.append(path)
        if mixed:
            return CriterionResult(
                "M23", title, FAIL, "Data and schema mixed: " + self.listing(mixed)
            )
        return CriterionResult("M23", title, PASS)

    # Performance and delivery format

    def query_count_tests(self) -> CriterionResult:
        title = "Query-count test for changed views"
        views = [p for p in self.added if self.is_view(p)]
        if not views:
            return CriterionResult("P3", title, PASS, "No view changed.")
        asserted = any(
            "assertNumQueries" in text
            for path, lines in self.added.items()
            if self.is_test(path)
            for _, text in lines
        )
        if asserted:
            return CriterionResult("P3", title, PASS)
        return CriterionResult(
            "P3", title, WARN, "No `assertNumQueries` added for: " + self.listing(views)
        )

    def branch_name(self) -> CriterionResult:
        branch = self.options.branch
        title = "Branch named `<issue>-<description>`"
        if not branch:
            return CriterionResult("D1", title, INFO, "No branch given.")
        if ISSUE_BRANCH.match(branch):
            return CriterionResult("D1", title, PASS)
        return CriterionResult("D1", title, WARN, f"`{branch}`")

    def no_merge_commits(self) -> CriterionResult:
        merges = self.scope.git(
            "log", "--merges", "--format=%h %s", f"{self.scope.merge_base}..HEAD"
        ).splitlines()
        title = "Rebased on main"
        if not merges:
            return CriterionResult("D2", title, PASS)
        return CriterionResult(
            "D2", title, WARN, "Merge commits: " + self.listing(merges)
        )

    def commit_messages(self) -> CriterionResult:
        title = "Meaningful commit messages"
        bad = [
            line
            for line in self.scope.commits.splitlines()
            if BAD_COMMIT_SUBJECT.match(line.partition(" ")[2].strip())
        ]
        if not bad:
            return CriterionResult("D3", title, PASS)
        return CriterionResult("D3", title, FAIL, self.listing(bad))

    def description(self) -> CriterionResult:
        title = "Description complete"
        if not self.options.title:
            return CriterionResult("D4", title, INFO, "No pull request given.")
        if not self.body.strip():
            return CriterionResult("D4", title, FAIL, "The description is empty.")
        missing = [
            name
            for name, pattern in DESCRIPTION_SECTIONS.items()
            if not pattern.search(self.body)
        ]
        if not missing:
            return CriterionResult("D4", title, PASS)
        return CriterionResult("D4", title, WARN, "Missing: " + ", ".join(missing))

    def not_draft(self) -> CriterionResult:
        if self.options.draft == "true":
            return CriterionResult("D8", "Not a draft", FAIL, "Still a draft.")
        if not self.options.title:
            return CriterionResult("D8", "Not a draft", INFO, "No pull request given.")
        return CriterionResult("D8", "Not a draft", PASS)

    # Report

    def render(self, results: list[CriterionResult]) -> str:
        counts = {s: sum(r.status == s for r in results) for s in (FAIL, WARN, PASS)}
        lines = [
            f"## Contribution check: {FAIL} {counts[FAIL]} failed · "
            f"{WARN} {counts[WARN]} to look at · {PASS} {counts[PASS]} passed",
            "",
            "_The mechanical part of `CONTRIBUTION_CRITERIA.md`; "
            f"{INFO} needs a human or could not be measured._",
            "",
            "| | ID | Criterion | Detail |",
            "|---|---|---|---|",
        ]
        for r in results:
            detail = r.detail.replace("|", "\\|").replace("\n", " ")
            lines.append(f"| {r.status} | {r.criterion} | {r.title} | {detail} |")
        for name, output in self.outputs.items():
            lines_of_output = output.strip().splitlines()
            shown = "\n".join(lines_of_output[:OUTPUT_LINES])
            if len(lines_of_output) > OUTPUT_LINES:
                shown += f"\n[{len(lines_of_output) - OUTPUT_LINES} more lines]"
            lines += [
                "",
                f"<details><summary>{name} output</summary>",
                "",
                "```",
                shown.replace("```", "'''"),
                "```",
                "",
                "</details>",
            ]
        return "\n".join(lines) + "\n"

    # Helpers

    @staticmethod
    def diff_lines(diff: str) -> Iterator[tuple[str, str, int, str]]:
        """Added and removed lines of a diff: path, sign, new line number, text.

        Removed lines carry the number of the next new line; only added lines'
        numbers are exact.
        """
        path = old_path = ""
        number = 0
        in_header = False
        for line in diff.splitlines():
            if line.startswith("diff --git "):
                in_header, path, old_path = True, "", ""
                continue
            if in_header:
                # Deleted files have "+++ /dev/null"; their lines count under
                # the old path, so a deleted test file is still seen.
                if line.startswith("--- a/"):
                    old_path = line[6:]
                elif line.startswith("+++ "):
                    path = line[6:] if line.startswith("+++ b/") else old_path
                hunk = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)", line)
                if hunk:
                    in_header = False
                    number = int(hunk.group(1))
                continue
            hunk = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)", line)
            if hunk:
                number = int(hunk.group(1))
                continue
            if not path:
                continue
            if line.startswith("+"):
                yield path, "+", number, line[1:]
                number += 1
            elif line.startswith("-"):
                yield path, "-", number, line[1:]
            elif line.startswith(" "):
                number += 1

    @staticmethod
    def count_effective_lines(path: str, lines: list[str]) -> int:
        """Added lines without blanks and comments, docstrings included."""
        suffix = Path(path).suffix
        count = 0
        in_block = False
        for raw in lines:
            text = raw.strip()
            if not text:
                continue
            if suffix == ".py":
                if in_block:
                    in_block = not text.endswith(('"""', "'''"))
                    continue
                if text.startswith(('"""', "'''")):
                    closed = len(text) >= 6 and text.endswith(text[:3])
                    in_block = not closed
                    continue
                if text.startswith("#"):
                    continue
            else:
                opener, closer = ("<!--", "-->") if suffix == ".html" else ("/*", "*/")
                if in_block:
                    in_block = closer not in text
                    continue
                if text.startswith(opener):
                    in_block = closer not in text
                    continue
                if suffix == ".html" and text.startswith("{#") and text.endswith("#}"):
                    continue
                if suffix == ".js" and text.startswith("//"):
                    continue
            count += 1
        return count

    @staticmethod
    def has_reason(text: str) -> bool:
        comment = text[text.index("#") :] if "#" in text else text
        rest = SUPPRESSION.sub("", comment)
        return bool(re.search(r"[A-Za-z]{3,}", rest))

    def added_matching(
        self, pattern: re.Pattern[str], tests: bool
    ) -> Iterator[tuple[str, int, str]]:
        for path, lines in self.added.items():
            if self.is_test(path) != tests or self.is_migration(path):
                continue
            for number, text in lines:
                if pattern.search(text):
                    yield path, number, text

    def new_migrations(self) -> list[str]:
        return sorted(
            p
            for p, s in self.statuses.items()
            if s == "A"
            and self.is_migration(p)
            and p.endswith(".py")
            and not p.endswith("__init__.py")
        )

    def app_of(self, path: str) -> str:
        depth = 3 if self.scope.prefix else 2
        return "/".join(path.split("/")[:depth])

    @staticmethod
    def counts_for_loc(path: str) -> bool:
        parts = Path(path).parts
        return Path(path).suffix in LOC_SUFFIXES and not any(
            part in LOC_EXCLUDED_PARTS for part in parts
        )

    @staticmethod
    def is_test(path: str) -> bool:
        return "/tests/" in f"/{path}"

    @staticmethod
    def is_migration(path: str) -> bool:
        return "/migrations/" in f"/{path}"

    @classmethod
    def is_view(cls, path: str) -> bool:
        return (
            path.endswith(".py")
            and not cls.is_test(path)
            and ("/views/" in path or Path(path).name.endswith("views.py"))
        )

    @classmethod
    def is_component(cls, path: str) -> bool:
        if (
            not path.endswith(".py")
            or cls.is_test(path)
            or path.endswith("__init__.py")
        ):
            return False
        return cls.is_view(path) or any(
            f"/{kind}/" in path or Path(path).name.endswith(f"{kind}.py")
            for kind in ("managers", "repositories")
        )

    @staticmethod
    def listing(items: list[str]) -> str:
        shown = ", ".join(items[:MAX_LISTED])
        rest = len(items) - MAX_LISTED
        return shown + (f" and {rest} more" if rest > 0 else "")

    @staticmethod
    def execute(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(  # noqa: S603  # nosec B603 - fixed command
            command, cwd=cwd, capture_output=True, text=True, check=False
        )


if __name__ == "__main__":
    sys.exit(ContributionCheck.main())
