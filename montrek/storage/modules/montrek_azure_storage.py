from azure.storage.blob import BlobPrefix
from storages.backends.azure_storage import AzureStorage


class MontrekAzureStorage(AzureStorage):
    """django-storages' Blob Storage backend, with Django's listdir().

    Django defines listdir(path) as the directories and files directly under
    `path`, named relative to it. django-storages (1.14.6) returns no
    directories and every blob under the prefix, recursively and by its full
    name, so code that walks the tree, such as StorageCleanup, asks for names
    that do not exist.
    """

    def listdir(self, path: str = "") -> tuple[list[str], list[str]]:
        prefix = self._get_valid_path(path) if path else ""
        if prefix and not prefix.endswith("/"):
            prefix += "/"
        directories: list[str] = []
        files: list[str] = []
        # With a delimiter, everything below the next "/" comes back as one
        # BlobPrefix: a directory.
        for item in self.client.walk_blobs(
            name_starts_with=prefix, delimiter="/", timeout=self.timeout
        ):
            name = item.name[len(prefix) :]
            if isinstance(item, BlobPrefix):
                directories.append(name.rstrip("/"))
            else:
                files.append(name)
        return directories, files
