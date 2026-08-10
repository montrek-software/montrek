from django.core.management import call_command
from django.core.management.base import BaseCommand

from code_generation.management.base.code_generation_command import (
    StdArgumentsMixin,
)


class Command(StdArgumentsMixin, BaseCommand):
    help = "Generate a full file export instance (registry, processor and views)."

    def handle(self, *args, **kwargs):
        std_args = [
            kwargs["app_path"],
            kwargs["prefix"],
        ]
        std_kwargs = {
            "replace": kwargs["replace"],
            "verbose": kwargs["verbose"],
        }
        call_command("generate_export_registry_hub_models", *std_args, **std_kwargs)
        call_command("generate_export_registry_sat_models", *std_args, **std_kwargs)
        call_command("generate_export_registry_repositories", *std_args, **std_kwargs)
        call_command("generate_export_registry_managers", *std_args, **std_kwargs)
        call_command("generate_export_processor", *std_args, **std_kwargs)
        call_command("generate_export_manager", *std_args, **std_kwargs)
        call_command("generate_export_registry_pages", *std_args, **std_kwargs)
        call_command("generate_export_registry_views", *std_args, **std_kwargs)
        call_command("generate_export_registry_urls", *std_args, **std_kwargs)
        call_command("generate_export_registry_urls_init", *std_args, **std_kwargs)
        call_command("generate_export_registry_hub_factories", *std_args, **std_kwargs)
        call_command("generate_export_registry_sat_factories", *std_args, **std_kwargs)
        call_command("generate_export_registry_view_tests", *std_args, **std_kwargs)
