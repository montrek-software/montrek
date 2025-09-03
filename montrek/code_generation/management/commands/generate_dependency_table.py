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
        self.add_view_test()

    def get_model_name(self, model: str) -> str:
        return model.replace("_", " ").title().replace(" ", "")

    def get_python_path(self, path: str) -> str:
        if path.endswith(os.path.sep):
            path = path[:-1]

        return path.replace(os.path.sep, ".")

    def _add_code(self, path: str, search_string: str, code: str):
        with open(path, "r") as f:
            old_code = f.read()
        if search_string in old_code:
            self.stdout.write(f"{search_string} exists already in {path}!")
            return
        new_code = old_code + code
        with open(path, "w") as f:
            f.write(new_code)
        self.stdout.write(f"Created {search_string} in {path}!")

    def add_view_test(self):
        test_path = os.path.join(
            self.path_out, "tests", "views", f"test_{self.model_out}_views.py"
        )
        class_name = f"Test{self.model_out_name}{self.model_in_name}sListView"
        code = f"""class {class_name}(vtc.MontrekListViewTestCase):
    viewname = "{self.model_out}_{self.model_in}s_list"
    view_class = views.{self.model_out_name}{self.model_in_name}sListView
    expected_no_of_rows = 5

    def build_factories(self):
        self.{self.model_out}_factory = {self.model_out_name}SatelliteFactory.create()
        {self.model_in_name}SatelliteFactory.create_batch(
            5, {self.model_out}=self.{self.model_out}_factory
        )
        other_{self.model_out}_factory = {self.model_out_name}SatelliteFactory.create()
        {self.model_in_name}SatelliteFactory.create_batch(
            5, {self.model_out}=other_{self.model_out}_factory
        )

    def url_kwargs(self):
        return {{"pk": self.{self.model_out}_factory.get_hub_value_date().pk}}"""
        self._add_code(test_path, class_name, code)
