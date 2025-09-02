import os
import re

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
        self.add_link_to_hub()

    def get_model_name(self, model: str) -> str:
        return model.replace("_", " ").title().replace(" ", "")

    def add_link_to_hub(self):
        hub_file_path = os.path.join(
            self.path_in, "models", f"{self.model_in}_hub_models.py"
        )
        link_field_name = f"link_{self.model_in}_{self.model_out}"
        link_related_field_name = f"link_{self.model_out}_{self.model_in}"
        with open(hub_file_path, "r") as f:
            code = f.read()
        first_line = f"{link_field_name} = models.ManyToManyField("
        second_line = rf""" "{self.model_out_name}Hub",
        through="Link{self.model_in_name}{self.model_out_name}",
        related_name="{link_related_field_name}",
    )
    """
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
        models_import_satement = "from django.db import models\n"
        if models_import_satement not in new_code:
            new_code = "from django.db import models\n" + new_code
        with open(hub_file_path, "w") as f:
            f.write(new_code)
