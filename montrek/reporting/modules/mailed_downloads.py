"""Tables too large to download directly are stored here and mailed as a link.

Each file lives in the default storage under
`reporting_downloads/<user id>/<download id>/<file name>`. The link carries only
the download id and the file name; the view puts in the id of the logged-in
user, so a link only works for the user it was sent to and cannot name any
other file.
"""

import uuid

from django.core.files.base import File
from django.core.files.storage import default_storage

STORAGE_DIR = "reporting_downloads"


def storage_path(user_id: int, download_id: uuid.UUID, file_name: str) -> str:
    return f"{STORAGE_DIR}/{user_id}/{download_id}/{file_name}"


def file_name_for_link(name: str) -> str:
    """`name` as a single path segment, which the download URL requires."""
    return name.replace("/", "_").replace("\\", "_")


def store(user_id: int, file_name: str, content: File) -> uuid.UUID:
    """Store `content` for `user_id` and return the id its link names."""
    download_id = uuid.uuid4()
    default_storage.save(storage_path(user_id, download_id, file_name), content)
    return download_id


class SingleUseFile(File):
    """A stored download that deletes itself from the storage once closed.

    A FileResponse closes it after the last chunk has been sent, so the file
    is streamed instead of read into memory first, and is gone afterwards.
    """

    def __init__(self, path: str):
        super().__init__(default_storage.open(path, "rb"))
        self.storage_path = path

    def close(self) -> None:
        super().close()
        default_storage.delete(self.storage_path)
