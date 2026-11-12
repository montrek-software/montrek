from django.apps import apps
from django.core.management.base import BaseCommand, CommandError, CommandParser

from baseclasses.repositories.db.hub_value_date_copy import HubValueDateCopy


class Command(BaseCommand):
    help = (
        "Check value_date_copy of all hub value date models: every copy equals "
        "the date of its value date row and no hub has two rows on one date, "
        "so the latest row of each hub is the same by copy as by value date row. "
        "Fails if any check fails."
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
        failed = [
            finding
            for finding in HubValueDateCopy(app_labels).check()
            if not finding.is_consistent
        ]
        if not failed:
            self.stdout.write(self.style.SUCCESS("All hub value dates consistent."))
            return
        for finding in failed:
            label = finding.model._meta.label
            if not finding.has_column:
                self.stdout.write(
                    f"{label}: no value_date_copy column, its migration is missing"
                )
                continue
            self.stdout.write(
                f"{label}: {finding.stale_copies} stale copies, "
                f"{finding.hubs_with_duplicate_dates} hubs with duplicate dates"
            )
        raise CommandError(f"Inconsistent hub value dates in {len(failed)} model(s).")
