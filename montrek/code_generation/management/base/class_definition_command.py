import os
from django.core.management.base import BaseCommand
from jinja2 import Environment, FileSystemLoader
from code_generation import CODE_TEMPLATE_DIR
from code_generation.config.hub_models_config import ConfigBase


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


class CodeGenerationCommandBase(StdArgumentsMixin, BaseCommand):
    help: str = "Generate class definitions based on code template."
    config_class: type[ConfigBase] = ConfigBase

    def handle(self, *args, **kwargs):
        app_path = kwargs["app_path"].lower()
        prefix = kwargs["prefix"].lower()
        config = self.config_class(app_path, prefix)
        output_path = config.get_output_file_path()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # dotted_app_path = app_path.replace("/", ".")
        #
        # context = {
        #     "dotted_app_path": dotted_app_path,
        #     'hub_model_path': os.path.join(app_path, 'models', f'{prefix}_hub_models.py'),
        #     "hub_class_name": f"{prefix.capitalize()}Hub",
        #     "satellite_class_name": f"{prefix.capitalize()}Satellite",
        #     "repository_class_name": f"{prefix.capitalize()}Repository",
        #     "manager_class_name": f"{prefix.capitalize()}Manager",
        #     "page_class_name": f"{prefix.capitalize()}Page",
        #     "list_tab_id": f"tab_{prefix.lower()}_list",
        #     "list_tab_title": f"{prefix.capitalize()} List",
        # }

        env = Environment(loader=FileSystemLoader(CODE_TEMPLATE_DIR))
        template = env.get_template(config.template_file)
        rendered_content = template.render(**config.get_template_context())

        msg = f"Generating code at '{output_path}'."
        self.stdout.write(self.style.SUCCESS(msg))

        with open(output_path, "w") as f:
            f.write(rendered_content)
            print(rendered_content)
