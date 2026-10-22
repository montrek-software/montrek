import os

from django.conf import settings
from django.core.files.storage import InMemoryStorage
from django.core.files.storage.memory import (  # type: ignore[attr-defined]  # missing from django-stubs
    InMemoryFileNode,
)
from django.test import override_settings


class ObjectStorage(InMemoryStorage):
    """In memory and without local paths or directories, as an object storage.

    InMemoryStorage itself still answers path() with a path under MEDIA_ROOT;
    backends such as S3, GCS or Azure Blob raise NotImplementedError instead.
    It also keeps directories, which exist() reports; on those backends a
    directory is only a prefix of the stored names, and exist() is False for
    it.
    """

    def path(self, name):
        raise NotImplementedError("This backend doesn't support absolute paths.")

    def exists(self, name):
        return isinstance(self._resolve(name, check_exists=False), InMemoryFileNode)

    def _relative_path(self, name):
        # InMemoryStorage resolves names through path() itself.
        return os.path.relpath(super().path(name), self.location)


# Code that goes past the storage API to the filesystem fails under it.
object_storage = override_settings(
    STORAGES={
        **settings.STORAGES,
        "default": {"BACKEND": "testing.decorators.object_storage.ObjectStorage"},
    }
)
