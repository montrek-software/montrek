from django.apps import AppConfig


class InfoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "info"

    def ready(self):
        from baseclasses.signals import document_downloaded

        from info.signals import store_in_download_registry

        document_downloaded.connect(
            store_in_download_registry, dispatch_uid="info_download_registry"
        )
