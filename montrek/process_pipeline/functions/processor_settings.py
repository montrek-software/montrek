"""TOML settings for functions classes.

Settings files ship next to the module that defines the functions class, in a
``settings/`` subfolder. A user either picks one of those by name or uploads a
TOML file of their own; :func:`resolve_settings` implements that choice.
"""

import inspect
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, cast

from django.core.files.storage import default_storage

SETTINGS_FILETYPE = "toml"


@dataclass
class SettingsData:
    name: str
    path: Path
    filetype: str = SETTINGS_FILETYPE

    def get_full_path(self) -> Path:
        return self.path / f"{self.name}.{self.filetype}"


def load_settings_file(file_path: str | Path) -> dict[str, Any]:
    """Load a TOML file that ships with the code, from disk."""
    with open(file_path, "rb") as settings_file:
        return tomllib.load(settings_file)


def load_stored_settings_file(storage_name: str) -> dict[str, Any]:
    """Load an uploaded TOML file back through the storage backend.

    Uploads are read by name rather than by filesystem path so that a Celery
    worker on another host — or a non-filesystem storage backend — can still
    reach the file the web process saved.
    """
    with default_storage.open(storage_name, "rb") as settings_file:
        return tomllib.load(settings_file)


class ProcessorSettingsMixin:
    """Mixin that binds TOML settings loading to a functions class.

    Inherit from this mixin when your functions class reads TOML settings. Set
    ``has_settings = True`` and use ``@classmethod`` for any processing function
    that needs to call ``cls.load_settings(name)``.

    Settings files are expected in a ``settings/`` subfolder next to the module
    that defines the class, unless ``get_settings_path`` is overridden.

    Set ``require_packaged_settings = False`` when the functions class expects
    users to supply their own settings file instead of picking a packaged one.
    """

    has_settings: ClassVar[bool] = True
    require_packaged_settings: ClassVar[bool] = True
    settings_folder_name: ClassVar[str] = "settings"

    @classmethod
    def get_settings_path(cls) -> Path:
        return Path(inspect.getfile(cls)).resolve().parent / cls.settings_folder_name

    @classmethod
    def get_available_settings(cls) -> list[SettingsData]:
        """Return all TOML settings files packaged with this functions class."""
        if not cls.has_settings:
            return []
        settings_folder = cls.get_settings_path()
        # Deliberately not created here: discovery must stay read-only so that
        # rendering settings choices works on a read-only deployment. glob()
        # yields nothing when the folder is absent, which the check below handles.
        settings_files = sorted(settings_folder.glob(f"*.{SETTINGS_FILETYPE}"))
        if not settings_files and cls.require_packaged_settings:
            raise FileNotFoundError(
                f"No .{SETTINGS_FILETYPE} settings files found in "
                f"'{settings_folder}'. Either add settings files to the folder, "
                f"or set `has_settings = False` or "
                f"`require_packaged_settings = False` on {cls.__name__}."
            )
        return [
            SettingsData(name=f.stem, path=f.parent, filetype=SETTINGS_FILETYPE)
            for f in settings_files
        ]

    @classmethod
    def get_settings_choices(cls) -> list[tuple[str, str]]:
        """Return Django choice tuples for the packaged settings files."""
        return [
            (setting.name, setting.name) for setting in cls.get_available_settings()
        ]

    @classmethod
    def load_settings(cls, settings_name: str) -> dict[str, Any]:
        """Load the packaged settings file called *settings_name*."""
        for setting in cls.get_available_settings():
            if setting.name == settings_name:
                return load_settings_file(setting.get_full_path())
        raise FileNotFoundError(
            f"No settings file '{settings_name}' found for {cls.__name__}."
        )


def resolve_settings(
    functions_class: type,
    settings_name: str | None = None,
    settings_file_name: str | None = None,
) -> dict[str, Any]:
    """Return the settings to run a processor function with.

    An uploaded settings file wins outright over a packaged one, so a user who
    brings their own configuration gets exactly what they uploaded. Returns an
    empty dict when the functions class has no settings and none were uploaded.

    *settings_file_name* is a name in the default storage, not a filesystem path.
    """
    if settings_file_name:
        return load_stored_settings_file(settings_file_name)
    if not getattr(functions_class, "has_settings", False):
        return {}
    if not settings_name:
        raise KeyError(
            f"{functions_class.__name__} has has_settings = True, so a settings "
            "name or an uploaded settings file is required."
        )
    # has_settings = True is the contract that the class mixes in ProcessorSettingsMixin.
    settings_class = cast(type[ProcessorSettingsMixin], functions_class)
    return settings_class.load_settings(settings_name)
