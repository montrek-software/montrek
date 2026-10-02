from django.apps import apps
from django.core.management.base import BaseCommand, CommandError, CommandParser

from baseclasses.repositories.db.overlap_checker import find_overlapping_versions


class Command(BaseCommand):
    help = (
        "Report satellite versions and scalar links that are valid at the same "
        "time for the same hub. Repositories join the valid row, so such "
        "overlaps duplicate rows in their querysets. Fails if any are found."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "app_labels",
            nargs="*",
            help="Only check models of these apps (default: all apps).",
        )

    def handle(self, *args, **options) -> None:
        app_labels = tuple(options["app_labels"])
        # A misspelled label would select no models and report success.
        for app_label in app_labels:
            try:
                apps.get_app_config(app_label)
            except LookupError as error:
                raise CommandError(f"Unknown app label: {app_label}") from error
        findings = find_overlapping_versions(app_labels)
        if not findings:
            self.stdout.write(self.style.SUCCESS("No overlapping versions found."))
            return
        for finding in findings:
            keys = ", ".join(str(key) for key in finding.key_values)
            self.stdout.write(
                f"{finding.model._meta.label}: overlapping versions for "
                f"{finding.key_field} {keys}"
            )
        raise CommandError(
            f"Overlapping versions found in {len(findings)} model field(s)."
        )
