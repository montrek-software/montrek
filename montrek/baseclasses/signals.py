import sys

from baseclasses.repositories.db.hub_value_date_copy import HubValueDateCopy


def fill_hub_value_date_copies(verbosity: int = 1, **kwargs) -> None:
    """After every migrate: rows written before ``value_date_copy`` existed
    get their copy, so no app needs a data migration for it, and tables
    without statistics on the copy are analyzed."""
    hub_value_date_copy = HubValueDateCopy()
    filled = hub_value_date_copy.fill()
    analyzed = hub_value_date_copy.analyze()
    stdout = kwargs.get("stdout") or sys.stdout
    if verbosity < 1:
        return
    for model, rows in filled.items():
        if rows:
            stdout.write(
                f"  Filled value_date_copy of {rows} {model._meta.label} row(s)\n"
            )
    for model in analyzed:
        stdout.write(f"  Analyzed {model._meta.label}\n")
