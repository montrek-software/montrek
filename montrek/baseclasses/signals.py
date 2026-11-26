import sys

from django.dispatch import Signal

from baseclasses.repositories.db.database_schema import DatabaseSchema
from baseclasses.repositories.db.hub_value_date_copy import HubValueDateCopy

# Sent by the base views for every document they hand out, with the keyword
# arguments ``session_data``, ``document_name`` and ``download_type`` (a
# ``DownloadType``). The info app records it in its download registry.
document_downloaded = Signal()


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


def create_database_schema(
    using: str = "default", verbosity: int = 1, **kwargs
) -> None:
    """Before every migrate: creates the DB_SCHEMA of the migrated database if
    it is missing, ahead of the table that records the migrations."""
    schema = DatabaseSchema(using)
    if schema.ensure() and verbosity >= 1:
        stdout = kwargs.get("stdout") or sys.stdout
        stdout.write(f"  Created schema {schema.name}\n")
