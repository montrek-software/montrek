from pathlib import Path, PurePosixPath

from baseclasses.utils import get_content_type
from django.conf import settings
from django.core.files.storage import default_storage


class MailAttachments:
    """The attachments of a mail, kept on it as a comma-separated list.

    An entry is the name of a file in the default storage. Code that sends a
    mail may also attach a local file by its absolute path; a person entering
    attachments in the send form is limited to the storage.
    """

    def __init__(self, attachments: str):
        self.entries = [
            entry.strip() for entry in attachments.split(",") if entry.strip()
        ]

    def to_email_attachments(self) -> list[tuple[str, bytes, str]]:
        return [self.to_email_attachment(entry) for entry in self.entries]

    def to_storage_names(self) -> str:
        """The entries as storage names, or ValueError for one outside the storage.

        Absolute paths under MEDIA_ROOT, as stored on older mails, are turned
        into the name they have in the storage.
        """
        return ",".join(self.to_storage_name(entry) for entry in self.entries)

    @classmethod
    def to_email_attachment(cls, entry: str) -> tuple[str, bytes, str]:
        return (Path(entry).name, cls.read(entry), get_content_type(entry))

    @staticmethod
    def read(entry: str) -> bytes:
        if Path(entry).is_absolute():
            return Path(entry).read_bytes()
        with default_storage.open(entry, "rb") as file:
            return file.read()

    @staticmethod
    def to_storage_name(entry: str) -> str:
        path = Path(entry)
        if path.is_absolute():
            media_root = Path(settings.MEDIA_ROOT).resolve()
            resolved = path.resolve()
            if not resolved.is_relative_to(media_root):
                raise ValueError(f"{entry} is not a stored file")
            name = resolved.relative_to(media_root).as_posix()
        else:
            name = entry
        if ".." in PurePosixPath(name).parts or not default_storage.exists(name):
            raise ValueError(f"{entry} is not a stored file")
        return name
