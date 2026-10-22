# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Montrek is a Django-based data management platform following a **data warehouse hub-satellite architecture**. It supports report generation, async task processing, REST API, optional Keycloak/OIDC auth, and LLM integrations. The working directory for all Django commands is `montrek/` (this directory), while the Makefile lives one level up (`../Makefile`).

## Commands

All `make` commands must be run from the project root (`../`).

### Local Development (non-Docker)

```bash
make local-init                          # Initialize pyenv virtualenv and install deps
make local-runserver                     # Start Django dev server
make sync-local-python-env               # Sync dependencies after requirements change
```

When running locally, start only the DB in Docker and set `DB_HOST=localhost` in `.env`:

```bash
docker compose up db -d
python manage.py migrate
python manage.py runserver 8000
```

### Docker

```bash
make docker-up                           # Start all containers (detached)
make docker-down                         # Stop all containers
make docker-restart                      # Restart containers
make docker-logs web                     # View logs for a service
make docker-build                        # Rebuild Docker images
make docker-django-manage <command>      # Run Django management command in container
```

### Database

```bash
make docker-db-backup                    # Backup database
make docker-db-restore                   # Restore database from backup
```

### Testing

Don't run the full test suite during development; it is slow, and it always runs before merging. Run only the tests affected by a change: the touched app, or a specific module/class/method (e.g. `manage.py test montrek_example.tests.repositories.test_montrek_example_repository.TestCrossSatelliteFilter`). For a change in a shared foundation (e.g. `baseclasses`), also run the tests of the apps that use the changed code most directly. Don't run everything.

Tests use Django's test runner with `coverage`. Run from `montrek/`:

```bash
# Run all tests
coverage run --rcfile=.coveragerc manage.py test

# Run tests for a specific app
coverage run --rcfile=.coveragerc manage.py test <app_name>

# Run tests in parallel
coverage run --rcfile=.coveragerc manage.py test --parallel

# Generate HTML coverage report
coverage html
```

Via Docker:

```bash
make docker-django-manage test
make docker-django-manage test <app_name>
```

### Linting & Formatting

All config is in `../pyproject.toml`. Line length is 88. Migrations and settings files are excluded from linting.

```bash
ruff check .                             # Lint
ruff check --fix .                       # Lint with auto-fix
ruff format .                            # Format (alternative to black)
black .                                  # Format
mypy .                                   # Type check
pre-commit run --all-files               # Run all pre-commit hooks manually
```

Pre-commit hooks run automatically on `git commit` and include: ruff, black, djlint (templates), bandit (security), mypy (whole project, using the local environment), plus standard checks (trailing whitespace, YAML, debug statements).

Make sure that the produced code is ruff and sonarcube compliant

## Code Conventions

### Django ORM calls belong in repositories

- Before writing any query, check whether the framework mechanics already handle the task (`receive()`, `filter_by_linked_hub()`, `add_linked_satellites_field_annotations()` with `link_satellite_filter`/`cross_satellite_filters`, `create_by_dict()`, ...).
- If a direct Django ORM call (`Model.objects...`) is unavoidable, put it in the matching repository, or create a new repository for it. Never put one in managers, views, forms or modules.
- If the framework almost covers the task but needs a workaround or a direct ORM call, raise it as a possible framework enhancement instead of silently working around it.

### Modules are classes

- Write every new module (in `modules/`, or any helper module) as a class named after the module, e.g. `mail_attachments.py` → `MailAttachments`, `storage_cleanup.py` → `StorageCleanup`; no loose module-level functions. State goes into `__init__`; helpers that need none become `@staticmethod`/`@classmethod`.
- A resource that must be released (a temporary copy, an open handle) is a context manager class (`__enter__`/`__exit__`), not a `@contextmanager` function.
- Exceptions: Django's function-based conventions (migrations' `RunPython` functions, function views, signal receivers, template tags), and module-level constants.

### Comments

- Assume the reader can read Python. Comment only when it adds understanding beyond what the code says: intent, invariants, non-obvious constraints, why an alternative doesn't work.
- Comments describe the current state of the code, never its history. Don't explain what was changed or why it changed; that belongs in the commit message or PR.
- Names from `mt_*` apps (classes, functions, fields) may be confidential. Never mention them in comments or docstrings of framework code (any app that isn't an `mt_*` app); use neutral examples, e.g. from `montrek_example`, instead. Code inside an `mt_*` app may reference its own classes and those of other `mt_*` apps.

## Architecture

### Directory Layout

```
<project root>/          # Makefile, .env, docker-compose.yml, pyproject.toml
└── montrek/             # Django project root (manage.py, .coveragerc)
    ├── montrek/         # Main Django package (settings.py, urls.py, celery.py)
    ├── baseclasses/     # Foundation: abstract models, base views, mixins, utils
    ├── user/            # Custom user model (MontrekUser)
    ├── reporting/       # Report generation (LaTeX, data tables, downloads)
    ├── tasks/           # Celery task tracking models
    ├── storage/         # File storage management
    ├── file_upload/     # File upload handling and DownloadRegistry
    ├── requesting/      # Request/workflow management
    ├── mailing/         # Email utilities
    ├── layout/          # Dashboard and UI layout configuration
    ├── docs_framework/  # Dynamic documentation pages
    ├── montrek_docs/    # Built-in help/documentation
    ├── info/            # Metadata and download registry storage
    ├── code_generation/ # Automatic code generation from templates
    ├── data_import/     # Data import utilities and API integrations
    ├── rest_api/        # REST API endpoints (JWT via SimpleJWT)
    ├── middleware/      # LoginRequired, PermissionError, MontrekError middleware
    ├── testing/         # Shared test utilities, base test cases, decorators
    └── montrek_example/ # Example app demonstrating framework patterns
```

### App Discovery

`settings.py` auto-discovers Django apps by recursively scanning `BASE_DIR` for directories containing `apps.py`. Apps do **not** need to be manually registered in `INSTALLED_APPS` — they are picked up automatically via `get_montrek_extension_apps()`.

URL routing in `montrek/urls.py` similarly auto-discovers and includes each app's `urls.py`.

### Model Architecture (Hub-Satellite)

All domain models inherit from abstract base classes in `baseclasses/models.py`:

- **`MontrekHubABC`** (`TimeStampMixin` + `StateMixin` + `UserMixin`): Hub facts with timestamps, state validity period (`state_date_start`/`state_date_end`), and `created_by` user link.
- **`MontrekSatelliteABC`**: Satellite records that track slowly changing dimensions, linked back to a hub via `HubForeignKey`.
- **`TimeStampMixin`**: Adds `created_at` / `updated_at`.
- **`StateMixin`**: Adds `state_date_start`, `state_date_end`, `comment` for temporal validity.
- **`AlertMixin`**: Adds `alert_level` and `alert_message` for status tracking.

### Repositories & Query Pipeline

Domain queries are built by **repositories** (`*/repositories/*.py`), preferably through the annotation pipeline below. Direct ORM calls are the exception and also live in repositories (see Code Conventions). Pipeline: `MontrekRepository.set_annotations()` registers fields (via `add_satellite_fields_annotations`, `add_linked_satellites_field_annotations`, `add_linked_hub_id`, or `annotator.annotations[name] = SomeSubqueryBuilder(...)`) → `Annotator` collects them → `QueryBuilder.build_queryset()` applies them → each `SubqueryBuilder.build()` returns the expression.

- Most annotations are **correlated subqueries** — cheap individually, but they add up per row.
- **Filtering/ordering on an annotation re-runs its subquery per row.** To filter by a linked hub use `filter_by_linked_hub()` or a direct FK column (`hub_id`), not the annotation.
- Subclasses reuse a parent's `set_annotations()` and prune with `annotator.remove_annotations((...))` — each removed field is one subquery fewer.
- `queryset_aware=True` builders receive the intermediate queryset to pre-compute in Python and emit literal `Value()`s.

### Query Performance: SQL vs Python

Do set-based work (filter, sort, paginate, aggregate, join) in SQL — always. But a **display-only, per-row derived value** is often cheaper in Python:

- Postgres can't reference a sibling `SELECT` alias, so a Django annotation referencing **other annotations** re-inlines their full SQL — duplicating expensive subqueries already selected as columns. A `CASE` over two expensive annotations can double the query.
- Move such a value to Python **only if** it's never used in `.filter()`/`.order_by()`/`.aggregate()`, its inputs are already-selected columns, and the row set is bounded. Compute it in the table element's `get_value()`.
- When porting SQL→Python, mirror SQL semantics exactly: NULL comparisons (`NOT (x = NULL)` is NULL, not `True`) and rounding mode (Postgres half-away-from-zero vs Python banker's `round()`).
- Verify with `len(str(qs.query))` + `SELECT` count before/after, and `qs.explain(analyze=True)`.

### View Architecture

Base views in `baseclasses/views/` provide permissions, form handling, and HTMX support:

- `MontrekTemplateView`, `MontrekDetailView`, `MontrekListView`
- `MontrekCreateView`, `MontrekUpdateView`, `MontrekDeleteView`
- `MontrekReportView` — report generation with optional HTMX
- `MontrekApiViewMixin` — REST API mixin

### Async Tasks (Celery)

Three worker queues defined in `montrek/celery.py` and `settings.py`:

| Queue              | Purpose                              |
| ------------------ | ------------------------------------ |
| `SEQUENTIAL_QUEUE` | Long-running, must run one at a time |
| `PARALLEL_QUEUE`   | Parallel-safe tasks                  |
| `FAST_QUEUE`       | Short, quick tasks; runs on the parallel worker unless the optional fast worker is enabled (`ENABLE_FAST_WORKER`) |

Tasks are auto-discovered from each app's `tasks.py` using `@shared_task`.

### App Convention

Apps are organised in packages, with one module per entity (`<prefix>`, snake_case). This is the layout the code generators produce:

```
app_name/
├── apps.py                 # MontrekAppConfig with the app's access policy
├── models/
│   ├── __init__.py         # re-exports the models
│   ├── <prefix>_hub_models.py      # hub, hub value date, links
│   └── <prefix>_sat_models.py      # satellites
├── repositories/
│   └── <prefix>_repositories.py    # queries (annotation pipeline, ORM calls)
├── managers/
│   └── <prefix>_managers.py        # business logic, table/report managers
├── forms/
│   └── <prefix>_forms.py
├── pages/
│   └── <prefix>_pages.py
├── views/
│   ├── __init__.py
│   └── <prefix>_views.py
├── urls/
│   ├── __init__.py         # collects the urlpatterns of the modules
│   └── <prefix>_urls.py
├── tests/
│   ├── factories/
│   │   ├── <prefix>_hub_factories.py
│   │   └── <prefix>_sat_factories.py
│   ├── managers/
│   ├── repositories/
│   └── views/
│       └── test_<prefix>_views.py
└── migrations/
```

File uploads and exports add `<prefix>_registry_*` / `<prefix>_export_registry_*` modules (plus a processor and an upload/export manager in `managers/`) to the same packages. Some older apps still use flat modules (`models.py`, `views.py`, ...); follow the existing layout of the app you work in.

#### Code generation

Prefer the `code_generation` management commands when introducing new montrek structures, and adapt the generated code afterwards rather than writing the boilerplate by hand. Run them from `montrek/`:

| Command | Generates |
| --- | --- |
| `start_montrek_app <name> --access open\|restricted [-p <dir>] [--permissions <dotted.path>]` | a new app with its `MontrekAppConfig` and access policy |
| `generate_table <app_path> <Prefix>` | a full entity: hub + satellite models, repository, managers, pages, forms, views, urls, factories and view tests |
| `generate_link <path_in> <model_in> <path_out> <model_out>` | a `MontrekOneToManyLinkABC` link between two hubs, plus the repository annotation and factory post-generation hook; change the base class if a different cardinality is needed |
| `generate_file_upload <app_path> <Prefix>` | a file upload registry with processor, upload manager, views and tests |
| `generate_file_export <app_path> <Prefix>` | a file export registry with processor, export manager, views and tests |

The building-block commands those wrap (`generate_hub_models`, `generate_repositories`, `generate_views`, ...) can be run individually. By default generated code is appended to existing files; `--replace` overwrites them.

### Environment Configuration

All configuration is via `.env` (one level up, in the project root). See `.env.template` for all required variables. Key variables: `SECRET_KEY`, `DEBUG`, `DB_ENGINE` (postgresql/mariadb), `DB_HOST`, `PROJECT_NAME`, `DEPLOY_HOST`.

### Authentication

Supports two modes configured via `.env`:

- **Django built-in** auth (default)
- **OIDC** (`ENABLE_OIDC=true` + `OIDC_ISSUER_URL`) — any OpenID provider, endpoints from its discovery document (`user/modules/oidc_provider.py`), via `mozilla-django-oidc`. `ENABLE_KEYCLOAK=true` also runs Keycloak with the install and, without an issuer URL, uses its realm at `auth-<PROJECT_NAME>.<DEPLOY_HOST>`. Code checks `settings.ENABLE_OIDC`, not `ENABLE_KEYCLOAK`.
