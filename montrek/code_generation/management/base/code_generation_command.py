import os
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


class CodeGenerationCommandBase(StdArgumentsMixin, BaseCommand):
    help: str = "Generate class definitions based on code template."

    def handle(self, *args, **kwargs):
        app_path = kwargs["app_path"].lower()
        prefix = kwargs["prefix"].lower()
        config = CodeGenerationConfig(app_path, prefix)
        output_path = config.output_paths[self.key]
        msg = f"Generating code at '{output_path}'."
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        env = Environment(loader=FileSystemLoader(CODE_TEMPLATE_DIR))
        template = env.get_template(config.template_files[self.key])
        rendered_content = template.render(**config.context)
        self.stdout.write(self.style.SUCCESS(msg))

        # TODO: check why flag is not working
        mode = "w" if kwargs["replace"] else "a"

        with open(output_path, mode) as f:
            f.write(rendered_content)
            print(rendered_content)
