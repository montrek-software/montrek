from django.apps import AppConfig


class DataImportTestingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "data_import.testing"
    label = "data_import_testing"
