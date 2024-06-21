from django.core.management.base import BaseCommand
from jinja2 import Environment, FileSystemLoader
from code_generation import CODE_TEMPLATE_DIR


class Command(BaseCommand):
    template_file: str = "hub_models.py.j2"
    help: str = (
        f"Generate hub model definitions based on '{template_file}' code template."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "hub_name",
            type=str,
            help="Name of the hub model to generate.",
        )
        # TODO: get output path based on app name?
        parser.add_argument(
            "output_path",
            type=str,
            help="Relative path to save the generated code.",
        )

    def handle(self, *args, **kwargs):
        hub_name = kwargs["hub_name"]
        output_path = kwargs["output_path"]

        env = Environment(loader=FileSystemLoader(CODE_TEMPLATE_DIR))
        template = env.get_template(self.template_file)
        rendered_content = template.render(hub_name=hub_name)

        with open(output_path, "w") as f:
            f.write(rendered_content)

        msg = f"Successfully generated code at '{output_path}'."
        self.stdout.write(self.style.SUCCESS(msg))
