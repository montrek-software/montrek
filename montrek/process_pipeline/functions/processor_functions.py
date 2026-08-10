"""Building blocks for pipelines that dispatch to a user-selected function.

A *functions class* groups the operations a user can pick from in the UI. Each
selectable operation is a ``staticmethod`` or ``classmethod`` decorated with a
return-type decorator built by :func:`return_with_type`. The decorator marks the
function as selectable and wraps its result in a :class:`ProcessorReturn`, so the
processor knows how to turn the result into a file.

Each domain defines its own return-type enum, e.g.::

    class ReportReturnType(Enum):
        PDF = "pdf"
        XLSX = "xlsx"

    return_pdf = return_with_type(ReportReturnType.PDF)

    class MyReports:
        label = "My Reports"
        description = "..."
        has_settings = False

        @staticmethod
        @return_pdf
        def portfolio_overview(session_data: dict, settings: dict) -> bytes: ...
"""

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any, ClassVar, Protocol

PROCESSOR_FUNCTION_MARKER = "_is_processor_function"


@dataclass
class ProcessorReturn:
    """Result of a processor function together with the file type to build."""

    data: Any
    return_type: Enum


class ProcessorFunctionsProtocol(Protocol):
    """Protocol for classes that group selectable processor functions.

    Concrete implementations should:

    - Set ``label`` and ``description`` as class-level string attributes.
      ``label`` is shown when selecting a functions class, ``description`` can be
      used in tooltips or documentation pages.
    - Expose processing logic as methods decorated with a return-type decorator
      built by :func:`return_with_type`.
    - Set ``has_settings`` to ``True`` and inherit
      ``process_pipeline.functions.processor_settings.ProcessorSettingsMixin``
      when the functions read TOML settings.

    Optionally define ``function_labels`` to override the labels derived from the
    function names.
    """

    label: ClassVar[str]
    description: ClassVar[str]
    has_settings: ClassVar[bool]


def return_with_type(return_type: Enum) -> Callable:
    """Build a decorator that tags a function as selectable and types its result."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return ProcessorReturn(data=func(*args, **kwargs), return_type=return_type)

        setattr(wrapper, PROCESSOR_FUNCTION_MARKER, True)
        return wrapper

    return decorator


def is_processor_function(func: Any) -> bool:
    """Return whether *func* was decorated with a :func:`return_with_type` decorator."""
    return bool(getattr(func, PROCESSOR_FUNCTION_MARKER, False))


def get_processor_functions(functions_class: type) -> list[tuple[str, Callable]]:
    """Return the ``(name, function)`` pairs a user may select on *functions_class*."""
    members = inspect.getmembers(
        functions_class,
        predicate=lambda f: inspect.isfunction(f) or inspect.ismethod(f),
    )
    return [member for member in members if is_processor_function(member[1])]


def get_function_names(functions_class: type) -> list[str]:
    """Return the names of the selectable functions on *functions_class*."""
    return [name for name, _ in get_processor_functions(functions_class)]


def get_function_label(functions_class: type, function_name: str) -> str:
    """Return the UI label for *function_name*.

    Falls back to a title-cased version of the function name unless the functions
    class maps the name to a label in ``function_labels``.
    """
    labels = getattr(functions_class, "function_labels", {})
    return labels.get(function_name, function_name.replace("_", " ").title())


def get_function_choices(functions_class: type) -> list[tuple[str, str]]:
    """Return Django choice tuples for the selectable functions of *functions_class*."""
    return [
        (name, get_function_label(functions_class, name))
        for name in get_function_names(functions_class)
    ]


def get_processor_function(functions_class: type, function_name: str) -> Callable:
    """Return the selectable function *function_name* of *functions_class*.

    Raises ``KeyError`` when the name is unknown or not selectable, so a tampered
    form submission cannot reach an arbitrary attribute of the functions class.
    """
    if function_name not in get_function_names(functions_class):
        raise KeyError(
            f"'{function_name}' is not a processor function of "
            f"{functions_class.__name__}."
        )
    return getattr(functions_class, function_name)
