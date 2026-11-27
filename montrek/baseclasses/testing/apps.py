from django.apps import AppConfig


class BaseclassesTestingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "baseclasses.testing"
    label = "baseclasses_testing"
