# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Montrek is a Django-based data management platform following a **data warehouse hub-satellite architecture**. It supports report generation, async task processing, REST API, optional Keycloak/OIDC auth, and LLM integrations. The working directory for all Django commands is `montrek/` (this directory), while the Makefile lives one level up (`../Makefile`).

## Commands

All `make` commands must be run from the project root (`../`), i.e. `montrek_competo/`.

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

Pre-commit hooks run automatically on `git commit` and include: ruff, black, djlint (templates), bandit (security), plus standard checks (trailing whitespace, YAML, debug statements).

Make sure that the produced code is ruff and sonarcube compliant

## Architecture

### Directory Layout

```
montrek_competo/         # Project root (Makefile, .env, docker-compose.yml, pyproject.toml)
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
    ├── montrek_example/ # Example app demonstrating framework patterns
    ├── mt_competo/      # Extension: asset management (Company, Fund, Covenant, Contract)
    ├── mt_economic_common/ # Extension: economic data (country, currency, credit institutions, SDMX)
    ├── mt_llm/          # Extension: LLM/RAG integration (Ollama, LangChain, chatbots)
    └── mt_tools/        # Extension: utilities (Excel processor)
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

Domain queries are built by **repositories** (`*/repositories/*.py`), not ad-hoc ORM calls. Pipeline: `MontrekRepository.set_annotations()` registers fields (via `add_satellite_fields_annotations`, `add_linked_satellites_field_annotations`, `add_linked_hub_id`, or `annotator.annotations[name] = SomeSubqueryBuilder(...)`) → `Annotator` collects them → `QueryBuilder.build_queryset()` applies them → each `SubqueryBuilder.build()` returns the expression.

- Most annotations are **correlated subqueries** — cheap individually, but they add up per row.
- **Filtering/ordering on an annotation re-runs its subquery per row.** To filter by a linked hub use `filter_by_linked_hub()` or a direct FK column (`hub_id`), not the annotation.
- Subclasses reuse a parent's `set_annotations()` and prune with `annotator.remove_annotations((...))` — each removed field is one subquery fewer.
- `queryset_aware=True` builders receive the intermediate queryset to pre-compute in Python and emit literal `Value()`s (e.g. `DerivedDamageValueSubqueryBuilder`).

### Query Performance: SQL vs Python

Do set-based work (filter, sort, paginate, aggregate, join) in SQL — always. But a **display-only, per-row derived value** is often cheaper in Python:

- Postgres can't reference a sibling `SELECT` alias, so a Django annotation referencing **other annotations** re-inlines their full SQL — duplicating expensive subqueries already selected as columns. A `CASE` over `risk_values_count`/`derived_damage_value` can double the query.
- Move such a value to Python **only if** it's never used in `.filter()`/`.order_by()`/`.aggregate()`, its inputs are already-selected columns, and the row set is bounded. Compute it in the table element's `get_value()` (see `compute_risk_value_status`, `compute_risk_profile_status_tag`).
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
| `FAST_QUEUE`       | Short, quick tasks                   |

Tasks are auto-discovered from each app's `tasks.py` using `@shared_task`.

### App Convention

Each app typically follows this structure:

```
app_name/
├── managers/               # Business logic (manager, repository, storage managers)
├── tests/
│   ├── factories/          # Factory Boy fixtures
│   ├── managers/
│   └── views/
├── migrations/
├── models.py
├── views.py
├── urls.py
├── forms.py
└── apps.py
```

### Environment Configuration

All configuration is via `.env` (one level up, at `montrek_competo/.env`). See `.env.template` for all required variables. Key variables: `SECRET_KEY`, `DEBUG`, `DB_ENGINE` (postgresql/mariadb), `DB_HOST`, `PROJECT_NAME`, `DEPLOY_HOST`.

### Authentication

Supports two modes configured via `.env`:

- **Django built-in** auth (default)
- **Keycloak/OIDC** (`USE_KEYCLOAK=true`) — integrates via `mozilla-django-oidc`
