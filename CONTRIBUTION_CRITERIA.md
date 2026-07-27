# Contribution Criteria — Acceptance Catalogue for Code Deliveries

**Applies to:** all code changes delivered by the Client for review and release under the
maintenance contract.
**Status:** binding annex to the maintenance contract.
**Version:** 1.0 — 2026-07-27

---

## 1. Purpose and Principle

The Contractor reviews and releases code that the Client develops. To keep review effort
predictable and the platform stable, every delivery must satisfy the criteria below
**before** it is handed in.

The guiding principle is:

> **The Client demonstrates that a change is correct. The Contractor verifies that
> demonstration.**

It is explicitly *not* the Contractor's task to reconstruct intent, write missing tests,
or repair failing checks. A delivery that does not meet the mandatory criteria in
Section 3 is returned unreviewed (see Section 8).

---

## 2. Definitions

| Term | Definition |
| --- | --- |
| **Delivery** | One pull request against `main` in the project repository. |
| **Issue** | One tracked ticket describing exactly one functional change, bug fix, or refactoring. |
| **Production code** | All source files that are not tests, not migrations, and not generated. Concretely: everything outside `*/tests/*`, `*/migrations/*`, and `*/factories/*`. |
| **Effective LOC** | Added + modified lines of production code, **excluding** blank lines and comment/docstring lines. Measurement method is defined in Section 4.2. |
| **Framework core** | `baseclasses/`, `middleware/`, `testing/`, `montrek/settings.py`, `montrek/urls.py`, `montrek/celery.py`. |
| **Mandatory criterion (M)** | Failure blocks review. The delivery is returned. |
| **Review criterion (R)** | Assessed by the Contractor with judgement. Failure leads to change requests. |

---

## 3. Mandatory Criteria (M) — Checked Before Review Begins

All of these are mechanically verifiable. The Client is expected to run them locally
before handing in; see the self-check in Section 9.

### 3.1 Scope and Size

| ID | Criterion |
| --- | --- |
| **M1** | The delivery references exactly **one** issue. The issue ID appears in the PR title. |
| **M2** | The delivery contains **no more than 400 effective LOC** (see Section 4). |
| **M3** | The delivery touches **no framework core** file (see Section 2) unless prior written agreement exists (Section 5.4). |
| **M4** | The delivery contains no unrelated changes: no opportunistic reformatting, no renaming outside the issue scope, no dependency bumps that the issue does not require. |

### 3.2 Build, Test, Coverage

| ID | Criterion |
| --- | --- |
| **M5** | The CI pipeline (`.github/workflows/django.yml`) passes green, without retries and without disabled or skipped tests. |
| **M6** | **Patch coverage ≥ 85 %**: of the effective LOC added or modified, at least 85 % are covered by automated tests. |
| **M7** | **Total coverage does not decrease** compared to the current `main`. |
| **M8** | No test is deleted, `@skip`-ed, `@expectedFailure`-ed, or moved to the `functional` tag in order to make the pipeline pass. Removing a test requires a written justification in the PR description. |
| **M9** | Every new or changed **view**, **manager**, and **repository** has at least one test. Views use the base test cases from `testing/test_cases/view_test_cases.py`; models and hubs/satellites use Factory Boy factories under `<app>/tests/factories/`. |

### 3.3 Static Analysis

| ID | Criterion |
| --- | --- |
| **M10** | `pre-commit run --all-files` passes clean. This covers **ruff** (`--fix`), **black**, **djlint**, **bandit**, plus trailing-whitespace, end-of-file, YAML, merge-conflict, and debug-statement checks. Configuration is authoritative in `../pyproject.toml` and `../.pre-commit-config.yaml`. |
| **M11** | No `# noqa`, `# type: ignore`, `# nosec`, or `djlint:off` is added without a one-line comment stating the reason. Blanket `# noqa` without a rule code is not accepted. |
| **M12** | Linter configuration (`pyproject.toml`, `.pre-commit-config.yaml`, `.coveragerc`) is not weakened. Loosening a rule is a framework-core change under M3. |
| **M13** | `mypy .` produces no new errors relative to `main`. |
| **M14** | The SonarQube quality gate passes; specifically **no new blocker or critical issues** and **no new security hotspots** left unreviewed. |

### 3.4 Security

| ID | Criterion |
| --- | --- |
| **M15** | No secrets, credentials, tokens, private keys, customer data, or production hostnames in the repository — including tests, fixtures, and commit history. |
| **M16** | No raw SQL and no string-interpolated queries. Database access goes through the Django ORM or the repository layer in `baseclasses/repositories/`. |
| **M17** | No `mark_safe`, `|safe`, `autoescape off`, `eval`, `exec`, `pickle.loads`, or `subprocess(shell=True)` on any input that can be influenced by a user, without prior written agreement. |
| **M18** | Every new view enforces authorisation. Views derive from the Montrek base views and set `permission_required`; API views additionally declare their authentication class. A view that is intentionally public is marked as such in the PR description. |
| **M19** | New or upgraded third-party dependencies are listed in the PR description with purpose, licence, and maintenance status. Dependencies are added to `requirements.in` and the lockfile is regenerated — never hand-edited. |

### 3.5 Data Model and Migrations

| ID | Criterion |
| --- | --- |
| **M20** | `python manage.py makemigrations --check --dry-run` reports no missing migrations. |
| **M21** | Migrations are additive and reversible. Destructive operations (`RemoveField`, `DeleteModel`, `AlterField` narrowing a type, data-truncating migrations) require prior written agreement. |
| **M22** | One delivery introduces at most one migration per app, and no migration file already merged to `main` is edited or renumbered. |
| **M23** | Data migrations are separated from schema migrations and are idempotent. |

---

## 4. The Size Limit in Detail

### 4.1 Rationale

The 400-LOC limit exists to keep review meaningful. Review quality degrades sharply above
roughly this size, and large deliveries make it impossible to attribute a regression to a
specific change. The limit is a **review-capacity limit, not a productivity limit** — the
Client may deliver as many compliant pull requests per week as they wish.

### 4.2 Measurement

Effective LOC are counted mechanically on the diff against the merge base, using `cloc`,
which excludes blank and comment lines by construction:

```bash
cloc --git --diff $(git merge-base HEAD origin/main) HEAD \
     --exclude-dir=migrations,tests,factories,static,node_modules \
     --include-lang=Python,HTML,JavaScript,CSS
```

The relevant figure is `added + modified` in the report total. Tests, factories,
migrations, comments, docstrings, blank lines, lockfiles, and translation files do not
count.

If `cloc` is unavailable, this approximation is accepted:

```bash
git diff $(git merge-base HEAD origin/main)..HEAD --numstat -- \
    ':!*/tests/*' ':!*/migrations/*' ':!*/factories/*' ':!*.lock' ':!requirements.txt' \
  | awk '{a+=$1} END {print a}'
```

### 4.3 Thresholds

| Effective LOC | Handling |
| --- | --- |
| **≤ 400** | Normal review, within the agreed turnaround. |
| **401 – 800** | Only after **prior** written agreement, obtained *before* development starts. Reviewed at the agreed additional rate. |
| **> 800** | Returned unreviewed and to be split into separate issues. |

**Exception — mechanical changes.** A change that is provably mechanical (a rename applied
by an IDE refactoring, an auto-formatting run, a generated file from `code_generation/`)
may exceed the limit if it is delivered as a **separate pull request that contains nothing
else**, and the PR description names the tool and command used.

---

## 5. Correct Use of the Montrek Framework (M / R)

Montrek is a framework, not a collection of Django apps. Changes that bypass it create
maintenance cost that the Client does not carry. The following are mandatory unless marked
otherwise.

### 5.1 Models — Hub / Satellite (M)

- Domain facts derive from `MontrekHubABC`; slowly-changing attributes go into a satellite
  derived from `MontrekSatelliteABC`, `MontrekTimeSeriesSatelliteABC`, or
  `MontrekTypeSatelliteABC`, linked via `HubForeignKey`.
- Relations between hubs use `MontrekOneToOneLinkABC` / `MontrekOneToManyLinkABC` /
  `MontrekManyToManyLinkABC`, not bare `ForeignKey` between hubs.
- Temporal validity is expressed through `StateMixin` (`state_date_start` /
  `state_date_end`), never through ad-hoc `valid_from` / `is_active` fields.
- Mutable attributes are **not** added directly to a hub in order to avoid creating a
  satellite.
- New apps follow the structure in `Checklists.md`, including hub factory, satellite
  factory, and model unit tests.

### 5.2 Views (M)

- Views derive from the Montrek base views in `baseclasses/views.py` —
  `MontrekListView`, `MontrekDetailView`, `MontrekCreateView`, `MontrekUpdateView`,
  `MontrekDeleteView`, `MontrekTemplateView`, `MontrekRestApiView`,
  `MontrekDownloadView`, `MontrekRedirectView` — not directly from Django's generic views
  and not as bare function views.
- HTMX partials use `MontrekHtmxRowRenderMixin` / `MontrekHtmxRowActionView` /
  `MontrekInlineFieldEditView` rather than hand-written partial rendering.
- URLs are registered in the app's own `urls.py` and picked up by auto-discovery; the
  central `montrek/urls.py` is not edited.

### 5.3 Business Logic (M)

- Business logic lives in `<app>/managers/` and data access in `<app>/repositories/`,
  following `baseclasses/managers/montrek_manager.py` and
  `baseclasses/repositories/montrek_repository.py`.
- Views and templates contain no business logic and no query construction. A view method
  longer than roughly 30 lines is a signal that logic belongs in a manager.
- Long-running work goes to Celery via `@shared_task` in the app's `tasks.py`, on the
  correct queue: `SEQUENTIAL_QUEUE` (must not run concurrently), `PARALLEL_QUEUE`, or
  `FAST_QUEUE`. Queue choice is justified in the PR description.

### 5.4 Framework Core (M)

Changes to `baseclasses/`, `middleware/`, `testing/`, `montrek/settings.py`,
`montrek/urls.py`, and `montrek/celery.py` are **reserved to the Contractor**. If the
Client needs a framework change, they open a separate issue describing the requirement;
the Contractor implements it or grants written permission to do so. A delivery mixing
framework-core changes with application changes is returned.

### 5.5 Conventions (R)

- Existing patterns win over personal preference. New code reads like the code around it.
- Reuse before reimplementation: check `baseclasses/utils.py`, `baseclasses/fields.py`,
  `baseclasses/forms.py`, `baseclasses/serializers.py`, and `testing/decorators/` before
  writing a new helper.
- Type hints on all new public functions, managers, and repository methods.
- Language of code, comments, docstrings, and commit messages is English.

---

## 6. Performance (M / R)

| ID | Criterion | Type |
| --- | --- | --- |
| **P1** | No N+1 queries. Related objects are loaded with `select_related` / `prefetch_related` or through the repository layer. | M |
| **P2** | No database query inside a loop and none inside a template. | M |
| **P3** | New or changed list and detail views have a query-count regression test using `assertNumQueries`. | M |
| **P4** | No unbounded query: list views paginate or filter; `.all()` without limit on a growable table is not accepted. | M |
| **P5** | Any new field used in a filter, ordering, or join has an index, or the PR states why none is needed. | R |
| **P6** | For changes to hot paths, the PR reports query count and wall time before and after. | R |
| **P7** | Bulk operations use `bulk_create` / `bulk_update` / `update()` rather than per-object saves in a loop. | R |

---

## 7. Delivery Format

| ID | Criterion |
| --- | --- |
| **D1** | One branch per issue, named `<issue-id>-<short-description>`, branched from current `main`. |
| **D2** | The branch is rebased on current `main` and free of merge conflicts at hand-in. |
| **D3** | Commits are atomic and have meaningful messages. No `wip`, `fix`, `asdf`, or `.` messages. |
| **D4** | The PR description contains: **what** changed, **why**, **how it was tested**, **what was deliberately not done**, and any **risk** the Contractor should look at. |
| **D5** | The PR description contains the completed self-check from Section 9. |
| **D6** | For UI changes: before/after screenshots. |
| **D7** | For behavioural changes: the affected documentation in `montrek_docs/` or `docs_framework/` is updated in the same delivery. |
| **D8** | The PR is not a draft and needs no verbal explanation to be understood. |

---

## 8. Review Process and Consequences

1. **Entry check.** The Contractor verifies the mandatory criteria (Section 3). This is
   mechanical and takes minutes.
2. **Return.** If a mandatory criterion fails, the delivery is returned with the failing
   criterion IDs and **without further review**. Returned deliveries are noted but not
   billed as review time.
3. **Review.** If the entry check passes, the Contractor reviews against the review
   criteria and issues change requests or approves.
4. **Release.** The Contractor merges and releases. Merging to `main` is reserved to the
   Contractor; the branch protection rule `no-commit-to-branch` is in force for everyone.
5. **Turnaround.** The agreed review turnaround applies **only** to deliveries that pass
   the entry check. It restarts when a returned delivery is handed in again.
6. **Repeated returns.** If the same delivery is returned three times for mandatory
   criteria, the underlying issue is re-planned jointly before further work.

**Emergency exception.** For a production-blocking incident, the Contractor may waive
M2 (size) and M6/M7 (coverage) on request. The waiver is recorded in the PR, and the
missing tests are delivered within five working days as a follow-up issue.

---

## 9. Self-Check Before Hand-In

The Client runs this and pastes the result into the PR description.

```bash
# from the repository root
pre-commit run --all-files                                  # M10, M11
cd montrek
mypy .                                                      # M13
python manage.py makemigrations --check --dry-run           # M20
coverage run --rcfile=.coveragerc manage.py test --parallel # M5
coverage report                                             # M6, M7
cd ..
cloc --git --diff $(git merge-base HEAD origin/main) HEAD \
     --exclude-dir=migrations,tests,factories,static,node_modules \
     --include-lang=Python,HTML,JavaScript,CSS               # M2
```

Checklist to copy into the PR description:

```markdown
## Delivery Self-Check

- [ ] One issue, referenced in the title (M1)
- [ ] Effective LOC: ____ / 400 (M2)
- [ ] No framework-core files touched (M3)
- [ ] No unrelated changes (M4)
- [ ] CI green, nothing skipped (M5, M8)
- [ ] Patch coverage: ____ % (≥ 85 %, M6) — total coverage before/after: ____ / ____ (M7)
- [ ] New views / managers / repositories are tested (M9)
- [ ] pre-commit clean (M10); every suppression justified (M11)
- [ ] mypy clean (M13); Sonar quality gate green (M14)
- [ ] No secrets, no raw SQL, permissions enforced (M15–M18)
- [ ] New dependencies documented; lockfile regenerated (M19)
- [ ] Migrations: checked, additive, reversible, one per app (M20–M23)
- [ ] Hub/satellite, base views, managers/repositories used correctly (Section 5)
- [ ] No N+1; `assertNumQueries` test present for changed list/detail views (P1–P4)
- [ ] Rebased on main, atomic commits, description complete (D1–D8)

**What changed and why:**
**How it was tested:**
**Deliberately not done:**
**Risks to look at in review:**
```

---

## 10. Changes to This Catalogue

This catalogue is versioned in the repository. Changes require written agreement between
both parties and take effect for deliveries started after the agreed date. Thresholds
(400 LOC, 85 % patch coverage) are reviewed jointly after the first three months of the
contract and adjusted on the basis of the review effort actually observed.
