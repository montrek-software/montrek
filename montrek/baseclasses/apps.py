from django.apps import AppConfig


class BaseclassesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "baseclasses"

    def ready(self):
        # Registers the access policy startup checks. Imported here rather than
        # at module level so that loading this app config does not pull in the
        # view layer (and with it the models it imports).
        from baseclasses import checks  # noqa: F401
