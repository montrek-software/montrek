import os
import re
from django.core.management.base import BaseCommand
from jinja2 import Environment, FileSystemLoader
from code_generation import CODE_TEMPLATE_DIR
from code_generation.config.code_generation_config import CodeGenerationConfig


class StdArgumentsMixin:
    def add_arguments(self, parser):
        parser.add_argument(
            "app_path",
            type=str,
            help="Path of app in which to save the generated code.",
        )
        parser.add_argument(
            "prefix",
            type=str,
            help="Prefix for the class name (e.g. 'Company').",
        )
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Replace existing files with generated code instead of appending.",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Print verbose output.",
        )


class CodeGenerationCommandBase(StdArgumentsMixin, BaseCommand):
    help: str = "Generate class definitions based on code template."

    def handle(self, *args, **kwargs):
        app_path = kwargs["app_path"].lower()
        prefix = self._convert_prefix_to_snake_case(kwargs["prefix"])
        verbose = kwargs["verbose"]
        config = CodeGenerationConfig(app_path, prefix)
        output_path = config.output_paths[self.key]
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        env = Environment(loader=FileSystemLoader(CODE_TEMPLATE_DIR), autoescape=True)
        template = env.get_template(config.template_files[self.key])
        rendered_content = template.render(**config.context)
        msg = f"Generating code at '{output_path}'."
        self.stdout.write(self.style.SUCCESS(msg))
        mode = "w" if kwargs["replace"] else "a"
        with open(output_path, mode) as f:
            f.write(rendered_content)
            if verbose:
                self.stdout.write(rendered_content)
        self._generate_init_files(output_path)

    def _generate_init_files(self, output_path):
        parts = output_path.split("/")
        current_path = ""
        for part in parts[:-1]:  # Exclude the last part because it's a file
            current_path = f"{current_path}/{part}" if current_path else part
            init_file_path = f"{current_path}/__init__.py"
            if not os.path.exists(init_file_path):
                self._generate_empty_init_file(init_file_path)

    def _generate_empty_init_file(self, output_path):
        try:
            with open(output_path, "w") as f:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Generating empty __init__.py at '{output_path}'."
                    )
                )
                f.write("")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to generate __init__.py: {e}"))

    def _convert_prefix_to_snake_case(self, prefix: str) -> str:
        # Use regular expressions to find all uppercase letters and replace them with an underscore followed by the lowercase letter
        return re.sub(r"(?<!^)([A-Z])", r"_\1", prefix).lower()
