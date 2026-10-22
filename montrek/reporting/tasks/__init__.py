# Imported here so that Celery's autodiscovery, which imports reporting.tasks,
# registers it.
from reporting.tasks.cleanup_task import reporting_storage_cleanup_task  # noqa: F401
