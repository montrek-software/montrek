import datetime
import os
from collections.abc import Iterator

from django.core.files.storage import FileSystemStorage, default_storage
from django.utils import timezone


class StorageCleanup:
    """Deletes the files under `directory` of the default storage once they
    were last modified more than `max_age` ago."""

    def __init__(self, directory: str, max_age: datetime.timedelta):
        self.directory = directory
        self.max_age = max_age

    def delete_old_files(self) -> int:
        """Returns the number of files deleted."""
        # Listed rather than checked with exists() first: on an object
        # storage the directory is only a prefix of the stored names, so
        # exists() is False for it even while files are stored under it.
        try:
            names = list(self._walk(self.directory))
        except FileNotFoundError:
            return 0
        cutoff = timezone.now() - self.max_age
        deleted = 0
        for name in names:
            if default_storage.get_modified_time(name) < cutoff:
                default_storage.delete(name)
                deleted += 1
        if isinstance(default_storage, FileSystemStorage):
            self._remove_empty_directories(default_storage.path(self.directory))
        return deleted

    def _walk(self, directory: str) -> Iterator[str]:
        subdirectories, files = default_storage.listdir(directory)
        for file_name in files:
            yield f"{directory}/{file_name}"
        for subdirectory in subdirectories:
            yield from self._walk(f"{directory}/{subdirectory}")

    @staticmethod
    def _remove_empty_directories(root: str) -> None:
        # Object storages have no directories; on a filesystem every stored
        # file leaves its own behind, one per download id. `root` itself stays.
        for current, _, _ in os.walk(root, topdown=False):
            if current != root and not os.listdir(current):
                os.rmdir(current)
