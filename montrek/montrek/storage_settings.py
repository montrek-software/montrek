"""The default storage, as STORAGE_BACKEND configures it.

A class of its own rather than code in settings.py, which runs only once per
process: the tests call it with a config of their own.
"""

import re
from typing import Any

from decouple import Config
from django.core.exceptions import ImproperlyConfigured

FILESYSTEM_BACKEND = "django.core.files.storage.FileSystemStorage"

_DOTTED_PATH = re.compile(r"^[A-Za-z_]\w*(\.[A-Za-z_]\w*)+$", re.ASCII)


class StorageSettings:
    def __init__(self, config: Config) -> None:
        self.config = config

    def default_storage(self) -> dict[str, Any]:
        """The STORAGES["default"] entry: where uploads, exports and other
        stored files go.

        Any backend other than the filesystem is the dotted path of a storage
        class, which an extension app provides. It is not imported here: the
        apps are not loaded yet while settings.py runs. The storage system
        check creates it once instead. The class reads its own settings, so it
        gets no options from here.
        """
        backend = self.config("STORAGE_BACKEND", default="filesystem")
        if backend == "filesystem":
            return {"BACKEND": FILESYSTEM_BACKEND}
        if not _DOTTED_PATH.match(backend):
            raise ImproperlyConfigured(
                "STORAGE_BACKEND must be filesystem or the dotted path of a "
                f"storage class, not {backend!r}."
            )
        return {"BACKEND": backend}
