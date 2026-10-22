import shutil
import tempfile
from pathlib import Path
from types import TracebackType

from django.core.files.storage import default_storage


class LocalStorageFile:
    """A local path of a file in the default storage, valid inside `with`.

    Some readers, such as pandas or openpyxl, take a path rather than a file
    object. A filesystem storage hands out the path of the stored file; any
    other backend gets the file copied into a temporary directory, removed on
    exit. The copy keeps the file name, since readers often go by its
    extension.
    """

    def __init__(self, name: str):
        self.name = name
        self._directory: tempfile.TemporaryDirectory[str] | None = None

    def __enter__(self) -> str:
        try:
            return default_storage.path(self.name)
        except NotImplementedError:
            pass
        self._directory = tempfile.TemporaryDirectory()
        copy_path = Path(self._directory.name) / Path(self.name).name
        with (
            default_storage.open(self.name, "rb") as source,
            copy_path.open("wb") as copy,
        ):
            shutil.copyfileobj(source, copy)
        return str(copy_path)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._directory is not None:
            self._directory.cleanup()
            self._directory = None
