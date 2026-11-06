# Contribution check

`make contribution-check` checks a branch against the mechanical part of
`CONTRIBUTION_CRITERIA.md` and prints a Markdown report: one row per criterion,
✅ passed, ❌ failed, ⚠️ needs a look, ℹ️ needs a human or could not be
measured. It works for core and for any `mt_*` extension under `montrek/`. In
the extensions' CI it runs after the tests of every pull request and posts the
report as one comment, which later runs update.

It reports only. With `--enforce` (in CI: the template input
`contribution_check_enforce`), a failed M criterion makes it exit with 1.

## Usage

Run from the project root; `git fetch` first.

```bash
make contribution-check                              # core branch against origin/main
make contribution-check REPO=mt_example              # an extension's branch
make contribution-check REPO=mt_example WORKTREE=true
make contribution-check COVERAGE_XML=path/coverage.xml
make contribution-check SKIP_PRE_COMMIT=true
```

It runs pre-commit, whose hooks fix files in place as on a commit, and
`manage.py makemigrations --check --dry-run`. Pull request data (title,
description, branch, draft) is only known in CI; locally those rows are ℹ️.

## What is checked

| ID | How |
| --- | --- |
| M1 | the title names an issue: `#123`, `123_...` or `ABC-123` |
| M2 | effective LOC: added lines of production Python, HTML, JS and CSS (outside `tests/`, `migrations/`, `factories/`, `static/`), without blank lines, comments and docstrings; ⚠️ above 400, ❌ above 800 |
| M3 | framework-core files (core only; an extension has none) |
| M5 | the result of the test run |
| M6 | patch coverage of the changed production lines, at least 85 % |
| M8 | removed `def test_...` and added `@skip`, `expectedFailure` or `functional` tags |
| M9 | ⚠️ when views, managers or repositories change without a test changing in the same app |
| M10 | pre-commit on the changed files; the catalogue's `--all-files` run is shown as ℹ️, because it also fails for code no change touched |
| M11 | added `noqa`, `type: ignore`, `nosec`, `djlint:off`: ❌ for a blanket `# noqa`, ⚠️ without a reason |
| M12 | ⚠️ when `pyproject.toml`, `.pre-commit-config.yaml`, `.coveragerc` or `setup.cfg` change |
| M16, M17 | ⚠️ for raw SQL, cursors, `mark_safe`, `\|safe`, `autoescape off`, `eval`, `exec`, `pickle.loads`, `shell=True` in added lines |
| M19 | ⚠️ when a requirements file or lock changes |
| M20 | `makemigrations --check --dry-run` |
| M21 | new migrations: ❌ for `RemoveField`/`DeleteModel` and `RunPython` without reverse, ⚠️ for `AlterField` and renames |
| M22 | ❌ for an edited or removed existing migration and more than one new migration per app |
| M23 | ❌ for a new migration that mixes `RunPython` and schema operations |
| P3 | ⚠️ when a view changes and no `assertNumQueries` is added |
| D1–D4, D8 | branch name, merge commits, commit messages like `wip` or `fix`, the description's sections, draft |

Not automated: M4, M7 (needs main's total coverage), M14 (see the SonarQube
comment), M18, the framework rules of section 5 and P1, P2, P4. These are what
the [AI review](ai_review.md) and the human review are for.
