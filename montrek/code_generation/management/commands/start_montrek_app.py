import os
import shutil

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        self.app_path: str = ""
        self.app_name: str = ""
        super().__init__(stdout, stderr, no_color, force_color)

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
        self.base_path = kwargs["path"].lower()
        self.app_name = kwargs["name"].lower()
        self.app_path = os.path.join(self.base_path, self.app_name)

        self._start_app()
        self._move_app()
        self._remove_files()

    def _start_app(self):
        call_command("startapp", self.app_name)

    def _move_app(self):
        shutil.move(self.app_name, self.base_path)

    def _remove_files(self):
        remove_files = ("tests.py", "models.py", "views.py")
        for rm_file in remove_files:
            os.remove(os.path.join(self.app_path, rm_file))
