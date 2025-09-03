import os
import re

from code_generation.management.commands.helper import ensure_method_with_code
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
        self.add_link_to_hub()
        self.add_link_to_repository()

    def get_model_name(self, model: str) -> str:
        return model.replace("_", " ").title().replace(" ", "")

    def get_python_path(self, path: str) -> str:
        if path.endswith(os.path.sep):
            path = path[:-1]
        return path.replace(os.path.sep, ".")

    def add_link_to_hub(self):
        hub_file_path = os.path.join(
            self.path_in, "models", f"{self.model_in}_hub_models.py"
        )
        link_field_name = f"link_{self.model_in}_{self.model_out}"
        link_related_field_name = f"link_{self.model_out}_{self.model_in}"
        with open(hub_file_path, "r") as f:
            code = f.read()
        first_line = f"{link_field_name} = models.ManyToManyField("
        second_line = (
            f"to={self.model_out_name}Hub,\n"
            f'    through="Link{self.model_in_name}{self.model_out_name}",\n'
            f'    related_name="{link_related_field_name}",\n'
            ")\n"
        )
        pattern_pass = rf"(class\s+{self.model_in_name}Hub\s*\(\s*MontrekHubABC\s*\)\s*:\s*\n)(\s*)pass\s*$"
        replacement_pass = rf"\1\2{first_line}\n\2    {second_line}"

        new_code, count = re.subn(
            pattern_pass, replacement_pass, code, flags=re.MULTILINE
        )

        if count == 0:
            # Case 2: class already has methods → insert after class definition line
            pattern_class = (
                rf"(class\s+{self.model_in_name}Hub\s*\(\s*MontrekHubABC\s*\)\s*:\s*\n)"
            )
            replacement_class = rf"\1    {first_line}\n        {second_line}\n"
            new_code, count = re.subn(
                pattern_class, replacement_class, code, count=1, flags=re.MULTILINE
            )
        link_class_lines = "\n\n" + "\n".join(
            [
                f"class Link{self.model_in_name}{self.model_out_name}(MontrekOneToManyLinkABC):",
                f"    hub_in = models.ForeignKey({self.model_in_name}Hub, on_delete=models.CASCADE)",
                f"    hub_out = models.ForeignKey({self.model_out_name}Hub, on_delete=models.CASCADE)",
            ]
        )
        new_code += link_class_lines
        import_statements = (
            "from django.db import models\n",
            "from baseclasses.models import MontrekOneToManyLinkABC\n",
            f"from {self.python_path_out}.models.{self.model_out}_hub_models import {self.model_out_name}Hub\n",
        )
        for statement in import_statements:
            if statement not in new_code:
                new_code = statement + new_code
        with open(hub_file_path, "w") as f:
            f.write(new_code)

    def add_link_to_repository(self):
        repo_path = os.path.join(
            self.path_in, "repositories", f"{self.model_in}_repositories.py"
        )
        repo_class_name = f"{self.model_in_name}Repository"
        code = f"""self.add_linked_satellites_field_annotations(
    {self.model_out_name}Satellite,
    Link{self.model_in_name}{self.model_out_name},
    ["hub_entity_id"],
    rename_field_map={{"hub_entity_id": "{self.model_out}_id"}}
)"""
        import_statements = (
            f"from {self.python_path_out}.models.{self.model_out}_sat_models import {self.model_out_name}Satellite\n",
            f"from {self.python_path_in}.models.{self.model_in}_hub_models import Link{self.model_in_name}{self.model_out_name}\n",
        )
        ensure_method_with_code(
            filename=repo_path,
            class_name=repo_class_name,
            method_name="set_annotations",
            code_to_insert=code,
            import_statements=import_statements,
        )
