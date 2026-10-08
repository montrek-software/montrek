from fnmatch import fnmatch
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, ClassVar

from django.apps import apps
from django.utils.module_loading import import_string

from baseclasses.errors.montrek_user_error import MontrekError

if TYPE_CHECKING:
    from file_upload.managers.file_upload_manager import FileUploadManagerABC


class UnknownUnattendedUploadError(MontrekError):
    """A key names no upload manager that allows unattended uploads."""


class UnattendedUploadRegistry:
    """Upload managers that may run without a person at the upload form.

    A manager opts in with ``allow_unattended_upload = True`` (see
    ``FileUploadManagerABC``), whose ``__init_subclass__`` then registers it
    here. Sources that feed uploads automatically, such as SFTP import sources,
    store the manager's key - its dotted path - and resolve it back with
    ``get_manager_class``.
    """

    _managers: ClassVar[dict[str, type["FileUploadManagerABC"]]] = {}

    @classmethod
    def key(cls, manager_class: type["FileUploadManagerABC"]) -> str:
        return f"{manager_class.__module__}.{manager_class.__qualname__}"

    @classmethod
    def register(cls, manager_class: type["FileUploadManagerABC"]) -> None:
        cls._managers[cls.key(manager_class)] = manager_class

    @classmethod
    def get_manager_class(cls, key: str) -> type["FileUploadManagerABC"]:
        """Resolve a stored key, importing the manager if not loaded yet.

        A Celery worker may not have imported the manager's module. The key
        comes from the database, so only modules of installed apps are
        imported, and only a class that opted in is returned.
        """
        if key not in cls._managers:
            cls._import_manager(key)
        try:
            return cls._managers[key]
        except KeyError:
            raise UnknownUnattendedUploadError(
                f"{key!r} is no upload that allows unattended uploads."
            ) from None

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        return sorted(
            (
                (key, manager_class.unattended_upload_label())
                for key, manager_class in cls._managers.items()
            ),
            key=lambda choice: choice[1].casefold(),
        )

    @classmethod
    def accepts_file(
        cls,
        manager_class: type["FileUploadManagerABC"],
        file_name: str,
        file_pattern: str = "*",
    ) -> bool:
        extension = PurePosixPath(file_name).suffix.lower()
        accepted = {ext.lower() for ext in manager_class.unattended_accept}
        return extension in accepted and fnmatch(file_name, file_pattern or "*")

    @classmethod
    def _import_manager(cls, key: str) -> None:
        module_name = key.rpartition(".")[0]
        if apps.get_containing_app_config(module_name) is None:
            return
        try:
            # Registers the manager through __init_subclass__ if it opted in
            import_string(key)
        except ImportError:
            return
