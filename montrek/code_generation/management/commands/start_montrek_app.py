import shutil

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "name",
            type=str,
            help="Name of the new name.",
        )
        parser.add_argument(
            "--path",
            action="store_true",
            help="Path of repository in which to generate the new app.",
        )

    def handle(self, *args, **kwargs):
        app_path = kwargs["path"].lower()
        app_name = kwargs["name"].lower()
        call_command("startapp", app_name)
        shutil.move(app_name, app_path)
