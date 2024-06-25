from django.core.management import call_command
from django.core.management.base import BaseCommand

from code_generation.management.base.class_definition_command import (
    StdArgumentsMixin,
)


class Command(StdArgumentsMixin, BaseCommand):
    def handle(self, *args, **kwargs):
        app_path = kwargs["app_path"]
        prefix = kwargs["prefix"]
        call_command("generate_hub_models", app_path, prefix)
        call_command("generate_satellite_models", app_path, prefix)
