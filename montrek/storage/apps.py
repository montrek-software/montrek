from django.apps import AppConfig


class StorageConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "storage"

    def ready(self):
        from storage import checks  # noqa: F401 - registers the check
