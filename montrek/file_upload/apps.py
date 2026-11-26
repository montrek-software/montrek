from django.apps import AppConfig


class FileUploadConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "file_upload"

    def ready(self):
        from baseclasses.view_plugins import ViewPlugins

        from file_upload.modules.simple_file_upload import SimpleFileUpload

        ViewPlugins.register_simple_file_upload(SimpleFileUpload())
