from collections.abc import Callable
from typing import Any, ClassVar, Protocol

from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from django.http.response import HttpResponseBase

from baseclasses.constants import PdfGenMethod
from baseclasses.typing import SessionDataType

# Renders the manager of a view as a PDF response, or returns None after adding
# the reason to the manager's messages.
PdfRenderer = Callable[[Any], HttpResponseBase | None]


class HistoryTableManagerProtocol(Protocol):
    def __init__(
        self, session_data: SessionDataType, title: str, queryset: Any
    ) -> None: ...


class SimpleFileUploadProtocol(Protocol):
    """The file upload a ``MontrekListView`` offers with ``do_simple_file_upload``."""

    def get_form(self, *args: Any) -> forms.Form: ...

    def upload(
        self,
        request: HttpRequest,
        session_data: SessionDataType,
        table_manager_class: type,
        view_kwargs: dict[str, Any],
    ) -> None: ...


class ViewPlugins:
    """Features of the base views that apps built on this one provide.

    The base views must not import those apps, so the apps register the
    features in their ``AppConfig.ready()``. A view that uses a feature whose
    app is not installed raises ``ImproperlyConfigured``.
    """

    _pdf_renderers: ClassVar[dict[PdfGenMethod, PdfRenderer]] = {}
    _history_table_manager_class: ClassVar[type[HistoryTableManagerProtocol] | None] = (
        None
    )
    _simple_file_upload: ClassVar[SimpleFileUploadProtocol | None] = None

    @classmethod
    def register_pdf_renderer(cls, method: PdfGenMethod, renderer: PdfRenderer) -> None:
        cls._pdf_renderers[method] = renderer

    @classmethod
    def render_pdf(cls, method: PdfGenMethod, manager: Any) -> HttpResponseBase | None:
        renderer = cls._pdf_renderers.get(method)
        if renderer is None:
            raise cls._missing(f"the {method.value} PDF export", "reporting")
        return renderer(manager)

    @classmethod
    def register_history_table_manager_class(
        cls, manager_class: type[HistoryTableManagerProtocol]
    ) -> None:
        cls._history_table_manager_class = manager_class

    @classmethod
    def history_table_manager_class(cls) -> type[HistoryTableManagerProtocol]:
        if cls._history_table_manager_class is None:
            raise cls._missing("the history table", "reporting")
        return cls._history_table_manager_class

    @classmethod
    def register_simple_file_upload(cls, upload: SimpleFileUploadProtocol) -> None:
        cls._simple_file_upload = upload

    @classmethod
    def simple_file_upload(cls) -> SimpleFileUploadProtocol:
        if cls._simple_file_upload is None:
            raise cls._missing("the simple file upload", "file_upload")
        return cls._simple_file_upload

    @staticmethod
    def _missing(feature: str, app: str) -> ImproperlyConfigured:
        return ImproperlyConfigured(
            f"No app provides {feature}: install the {app} app, which "
            "registers it in its AppConfig.ready()."
        )
