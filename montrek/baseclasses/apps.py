from django.apps import AppConfig


class BaseclassesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "baseclasses"

    def ready(self):
        # Registers the access policy startup checks. Imported here rather than
        # at module level so that loading this app config does not pull in the
        # view layer (and with it the models it imports).
        from baseclasses import checks  # noqa: F401
        from baseclasses import theme_checks  # noqa: F401
        from django.db.models.signals import post_migrate

        from baseclasses.field_encryption import use_field_encryption_key
        from baseclasses.signals import fill_hub_value_date_copies

        use_field_encryption_key()
        # Sent once per app; with this sender the copies are filled once
        post_migrate.connect(fill_hub_value_date_copies, sender=self)
