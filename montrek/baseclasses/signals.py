import sys

from baseclasses.repositories.db.hub_value_date_copy import HubValueDateCopy


def fill_hub_value_date_copies(sender, verbosity: int = 1, **kwargs) -> None:
    """After every migrate: rows written before ``value_date_copy`` existed
    get their copy, so no app needs a data migration for it."""
    filled = HubValueDateCopy().fill()
    stdout = kwargs.get("stdout") or sys.stdout
    for model, rows in filled.items():
        if rows and verbosity >= 1:
            stdout.write(
                f"  Filled value_date_copy of {rows} {model._meta.label} row(s)\n"
            )
