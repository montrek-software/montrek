"""Carrier for "which function should this pipeline run, with which settings".

The selection is made in a form and consumed by a processor that may well be
running in a Celery worker, so it has to survive a round trip through the task
broker. Celery is configured with the default JSON serializer here, which rules
out putting the functions class itself into ``pipeline_data`` — the class travels
as a dotted import path instead.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from django.utils.module_loading import import_string

from process_pipeline.functions.processor_functions import get_processor_function
from process_pipeline.functions.processor_settings import resolve_settings

FUNCTIONS_CLASS_KEY = "functions_class"
FUNCTION_KEY = "function"
SETTINGS_KEY = "settings"
SETTINGS_FILE_KEY = "settings_file_name"


def get_dotted_path(cls: type) -> str:
    return f"{cls.__module__}.{cls.__qualname__}"


@dataclass
class FunctionSelection:
    """What the user picked, in a form that survives JSON serialization."""

    functions_class_path: str
    function_name: str
    settings_name: str | None = None
    settings_file_name: str | None = None

    @classmethod
    def from_cleaned_data(
        cls,
        functions_class: type,
        cleaned_data: dict[str, Any],
        settings_file_name: str | None = None,
    ) -> "FunctionSelection":
        """Build a selection from a validated form's ``cleaned_data``."""
        return cls(
            functions_class_path=get_dotted_path(functions_class),
            function_name=cleaned_data[FUNCTION_KEY],
            settings_name=cleaned_data.get(SETTINGS_KEY) or None,
            settings_file_name=settings_file_name,
        )

    @classmethod
    def from_pipeline_data(cls, pipeline_data: dict[str, Any]) -> "FunctionSelection":
        return cls(
            functions_class_path=pipeline_data[FUNCTIONS_CLASS_KEY],
            function_name=pipeline_data[FUNCTION_KEY],
            settings_name=pipeline_data.get(SETTINGS_KEY),
            settings_file_name=pipeline_data.get(SETTINGS_FILE_KEY),
        )

    def to_pipeline_data(self) -> dict[str, Any]:
        return {
            FUNCTIONS_CLASS_KEY: self.functions_class_path,
            FUNCTION_KEY: self.function_name,
            SETTINGS_KEY: self.settings_name,
            SETTINGS_FILE_KEY: self.settings_file_name,
        }

    @property
    def functions_class(self) -> type:
        return import_string(self.functions_class_path)

    def get_function(self) -> Callable:
        return get_processor_function(self.functions_class, self.function_name)

    def get_settings(self) -> dict[str, Any]:
        return resolve_settings(
            self.functions_class,
            settings_name=self.settings_name,
            settings_file_name=self.settings_file_name,
        )
