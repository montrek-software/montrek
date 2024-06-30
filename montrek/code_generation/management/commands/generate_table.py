from django.core.management import call_command
from django.core.management.base import BaseCommand

from code_generation.management.base.code_generation_command import (
    StdArgumentsMixin,
)


class Command(StdArgumentsMixin, BaseCommand):
    def handle(self, *args, **kwargs):
        app_path = kwargs["app_path"]
        prefix = kwargs["prefix"]
        call_command("generate_hub_models", app_path, prefix)
        call_command("generate_satellite_models", app_path, prefix)
        call_command("generate_models_init", app_path, prefix)
        call_command("generate_repositories", app_path, prefix)
        call_command("generate_managers", app_path, prefix)
        call_command("generate_pages", app_path, prefix)
        call_command("generate_forms", app_path, prefix)
        call_command("generate_views_init", app_path, prefix)
        call_command("generate_views", app_path, prefix)
        call_command("generate_urls_init", app_path, prefix)
        call_command("generate_urls", app_path, prefix)
        call_command("generate_hub_factories", app_path, prefix)
        call_command("generate_sat_factories", app_path, prefix)
        call_command("generate_view_tests", app_path, prefix)
