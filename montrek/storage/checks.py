"""The default storage, created once by `manage.py check` and `migrate`.

settings.py only names the backend; Django imports and creates it on the first
file access. A wrong STORAGE_BACKEND, or a backend missing one of its own
settings, would then fail the first upload instead of the deploy, whose release
step runs `migrate`.
"""

from django.conf import settings
from django.core.checks import CheckMessage, Error, register
from django.core.files.storage import Storage, storages

HINT = "Check STORAGE_BACKEND and the settings its backend reads."


@register("montrek_storage")
def check_default_storage(app_configs=None, **kwargs) -> list[CheckMessage]:
    backend = settings.STORAGES["default"]["BACKEND"]
    # A new instance, not storages["default"], which stays cached. Any exception
    # counts: each backend reports a missing setting in its own way.
    try:
        storage = storages.create_storage(settings.STORAGES["default"])
    except Exception as error:
        return [
            Error(
                f"The default storage {backend} cannot be created: {error}",
                hint=HINT,
                id="storage.E001",
            )
        ]
    if not isinstance(storage, Storage):
        return [
            Error(
                f"The default storage {backend} is not a Django storage class.",
                hint=HINT,
                id="storage.E002",
            )
        ]
    return []
