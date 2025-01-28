from django.core.management import call_command
from django.core.management.base import BaseCommand

from code_generation.management.base.code_generation_command import (
    StdArgumentsMixin,
)
from code_generation.config.code_generation_config import CodeGenerationConfig


class Command(StdArgumentsMixin, BaseCommand):
    def handle(self, *args, **kwargs):
        std_args = [
            kwargs["app_path"],
            kwargs["prefix"],
        ]
        std_kwargs = {
            "replace": kwargs["replace"],
            "verbose": kwargs["verbose"],
        }
        call_command("generate_hub_models", *std_args, **std_kwargs)
        call_command("generate_satellite_models", *std_args, **std_kwargs)
        call_command("generate_models_init", *std_args, **std_kwargs)
        call_command("generate_repositories", *std_args, **std_kwargs)
        call_command("generate_managers", *std_args, **std_kwargs)
        call_command("generate_pages", *std_args, **std_kwargs)
        call_command("generate_forms", *std_args, **std_kwargs)
        call_command("generate_views_init", *std_args, **std_kwargs)
        call_command("generate_views", *std_args, **std_kwargs)
        call_command("generate_urls_init", *std_args, **std_kwargs)
        call_command("generate_urls", *std_args, **std_kwargs)
        call_command("generate_hub_factories", *std_args, **std_kwargs)
        call_command("generate_sat_factories", *std_args, **std_kwargs)
        call_command("generate_view_tests", *std_args, **std_kwargs)
        call_command("makemigrations")
        testcase = CodeGenerationConfig(
            kwargs["app_path"], kwargs["prefix"]
        ).output_paths["view_tests"]
        testcase = testcase.replace(".py", "").replace("/", ".")
        self.stdout.write(
            f"To run the test execute\n\tpython manage.py test {testcase}"
        )
