import os
from django.core.management.base import BaseCommand
from jinja2 import Environment, FileSystemLoader
from code_generation import CODE_TEMPLATE_DIR


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


class ClassDefinitionCommandBase(StdArgumentsMixin, BaseCommand):
    help: str = "Generate class definitions based on code template."

    def get_output_path(self, app_path: str, prefix: str) -> str:
        return os.path.join(app_path, self.get_output_path_in_app(prefix))

    def get_output_path_in_app(self, prefix: str) -> str:
        NotImplementedError("Subclasses must implement this method.")

    def handle(self, *args, **kwargs):
        app_path = kwargs["app_path"].lower()
        prefix = kwargs["prefix"].lower()

        output_path = self.get_output_path(app_path, prefix)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        context = {
            "hub_class_name": f"{prefix.capitalize()}Hub",
            "satellite_class_name": f"{prefix.capitalize()}Satellite",
            "repository_class_name": f"{prefix.capitalize()}Repository",
            "manager_class_name": f"{prefix.capitalize()}Manager",
        }

        env = Environment(loader=FileSystemLoader(CODE_TEMPLATE_DIR))
        template = env.get_template(self.template_file)
        rendered_content = template.render(**context)

        with open(output_path, "w") as f:
            f.write(rendered_content)

        msg = f"Successfully generated code at '{output_path}'."
        self.stdout.write(self.style.SUCCESS(msg))
