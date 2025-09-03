import os

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        self.model_in: str = ""
        self.model_out: str = ""
        self.path_in: str = ""
        self.path_out: str = ""
        super().__init__(stdout, stderr, no_color, force_color)

    def add_arguments(self, parser):
        parser.add_argument(
            "path_in",
            type=str,
            help="Path to app in which hub_in is located.",
        )
        parser.add_argument(
            "model_in",
            type=str,
            help="Model in in lowercase notation",
        )
        parser.add_argument(
            "path_out",
            type=str,
            help="Path to app in which hub_out is located.",
        )
        parser.add_argument(
            "model_out",
            type=str,
            help="Model out in lowercase notation",
        )

    def handle(self, *args, **kwargs):
        self.model_out = kwargs["model_out"]
        self.model_in = kwargs["model_in"]
        self.model_in_name = self.get_model_name(self.model_in)
        self.model_out_name = self.get_model_name(self.model_out)
        self.path_in = kwargs["path_in"]
        self.path_out = kwargs["path_out"]
        self.python_path_in = self.get_python_path(self.path_in)
        self.python_path_out = self.get_python_path(self.path_out)
        call_command(
            "generate_link", self.path_in, self.model_in, self.path_out, self.model_out
        )

    def get_model_name(self, model: str) -> str:
        return model.replace("_", " ").title().replace(" ", "")

    def get_python_path(self, path: str) -> str:
        if path.endswith(os.path.sep):
            path = path[:-1]

        return path.replace(os.path.sep, ".")
