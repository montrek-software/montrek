from code_generation.management.base.code_generation_command import StdArgumentsMixin
from django.core.management.base import BaseCommand


class Command(StdArgumentsMixin, BaseCommand):
    def handle(self, *args, **kwargs):
        self.stdout.write("Hello?")
