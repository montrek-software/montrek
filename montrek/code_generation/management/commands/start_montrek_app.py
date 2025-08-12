import os
import shutil

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        self.base_path: str = "."
        self.app_path: str = ""
        self.app_name: str = ""
        super().__init__(stdout, stderr, no_color, force_color)

    def add_arguments(self, parser):
        parser.add_argument(
            "name",
            type=str,
            help="Name of the new app.",
        )
        parser.add_argument(
            "-p",
            "--path",
            type=str,
            default=".",
            metavar="DIR",
            help="Path of repository in which to generate the new app.",
        )

    def handle(self, *args, **kwargs):
        # Normalize inputs
        self.base_path = kwargs["path"]
        self.app_name = kwargs["name"].lower()

        # Where the app will ultimately live
        self.app_path = os.path.join(self.base_path, self.app_name)

        # 1) Create the app in the current working directory
        self._start_app()

        # 2) Move it if a subfolder path was provided
        self._move_app()

        # 3) Fix AppConfig.name to include the dotted path (e.g., "pkg.subpkg.myapp")
        self._fix_app_config_name()

        # 4) Remove files we don't want
        self._remove_files()

    def _start_app(self):
        call_command("startapp", self.app_name)

    def _move_app(self):
        # Only move if target path is not the current directory
        if os.path.normpath(self.base_path) != os.path.normpath("."):
            os.makedirs(self.base_path, exist_ok=True)
            shutil.move(self.app_name, self.base_path)

    def _fix_app_config_name(self):
        apps_py = os.path.join(self.app_path, "apps.py")
        if not os.path.exists(apps_py):
            return  # Nothing to update (defensive)

        # Build dotted path: normalize first, then replace os.sep with '.'
        dotted_base = os.path.normpath(self.base_path)
        if dotted_base in (".", ""):
            dotted = self.app_name
        else:
            dotted = f"{dotted_base.replace(os.sep, '.')}.{self.app_name}"

        with open(apps_py, "r", encoding="utf-8") as f:
            content = f.read()

        # Replace the default `name = 'myapp'` with the dotted path
        # Be tolerant if quotes are double or single.

        content, n = re.subn(
            r"(^\s*name\s*=\s*['\"][^'\"]+['\"])",
            f"    name = '{dotted}'",
            content,
            flags=re.MULTILINE,
        )

        # If we didn't find a name line, append one inside the config class
        if n == 0:
            content = re.sub(
                r"(class\s+\w+Config\(AppConfig\):\s*\n)",
                r"\1    name = '" + dotted + r"'\n",
                content,
                flags=re.MULTILINE,
            )

        with open(apps_py, "w", encoding="utf-8") as f:
            f.write(content)

    def _remove_files(self):
        remove_files = ("tests.py", "models.py", "views.py")
        for rm_file in remove_files:
            path = os.path.join(self.app_path, rm_file)
            if os.path.exists(path):
                os.remove(path)
