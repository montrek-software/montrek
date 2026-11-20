from collections.abc import Iterator
from typing import Any

from django import forms
from django.http import HttpRequest
from django.utils.datastructures import MultiValueDict

from baseclasses.forms import MontrekParameterForm
from baseclasses.typing import SessionDataType

# GET parameter naming the parameter form that was submitted
SUBMITTED_FORM_PARAM = "parameter_form"
# Session key of the submitted inputs, by request path and form
SESSION_FIELD = "parameter_forms"
# Session key of the values the forms applied, by request path and form, for
# requests of other views that render rows of the page's table
VALUES_SESSION_FIELD = "parameter_values"


class ParameterForms:
    """Binds the parameter forms of a list view and hands their values to the
    session data.

    A submitted form is bound from the request and, if valid, stored for the
    page; otherwise the values stored for the page apply, or the initial ones.
    An invalid submission is shown with its errors and changes nothing.
    """

    def __init__(
        self,
        form_classes: tuple[type[MontrekParameterForm], ...],
        request: HttpRequest,
        persist: bool = True,
    ) -> None:
        self.form_classes = form_classes
        self.request = request
        # Without it the session is only read, as for the other table state
        self.persist = persist
        self.forms: list[MontrekParameterForm] = []

    @staticmethod
    def stored_values(session_data: SessionDataType, path: str) -> SessionDataType:
        """The values the parameter forms of the page at ``path`` applied, by
        session key, as the page's manager receives them."""
        return dict(session_data.get(VALUES_SESSION_FIELD, {}).get(path, {}))

    def update_session_data(self, session_data: SessionDataType) -> SessionDataType:
        stored = self._stored_for_path(SESSION_FIELD)
        stored_values = {}
        for form_class in self.form_classes:
            key = form_class.session_key
            shown_form, applied_form = self._bind(form_class, stored.get(key))
            if self._is_submitted(form_class) and shown_form.is_valid():
                stored[key] = self._submitted_data(shown_form)
            self.forms.append(shown_form)
            values = self._values(applied_form)
            session_data[key] = values
            # Initial values may be of any type; submitted ones are strings
            if applied_form.is_bound:
                stored_values[key] = values
            self._drop_request_params(session_data, shown_form)
        session_data.pop(SUBMITTED_FORM_PARAM, None)
        if self.persist and self.form_classes:
            self._store_for_path(SESSION_FIELD, stored)
            self._store_for_path(VALUES_SESSION_FIELD, stored_values)
        return session_data

    def _bind(
        self, form_class: type[MontrekParameterForm], stored_data: dict | None
    ) -> tuple[MontrekParameterForm, MontrekParameterForm]:
        """The form to show and the form whose values apply."""
        prefix = form_class.session_key
        # An empty submission is stored as well, e.g. an unchecked checkbox
        previous = (
            form_class(MultiValueDict(stored_data), prefix=prefix)
            if stored_data is not None
            else None
        )
        if previous is None or not previous.is_valid():
            # Stored values that no longer validate, e.g. a deleted choice
            previous = form_class(prefix=prefix)
        if not self._is_submitted(form_class):
            return previous, previous
        submitted = form_class(self.request.GET, prefix=prefix)
        if submitted.is_valid():
            return submitted, submitted
        return submitted, previous

    def _is_submitted(self, form_class: type[MontrekParameterForm]) -> bool:
        return self.request.GET.get(SUBMITTED_FORM_PARAM) == form_class.session_key

    @staticmethod
    def _input_names(form: MontrekParameterForm) -> Iterator[str]:
        """The names the form's inputs are submitted under. A multi-widget
        field, e.g. a date and a time, submits one per widget."""
        for name, field in form.fields.items():
            html_name = form.add_prefix(name)
            widget = field.widget
            if isinstance(widget, forms.MultiWidget):
                # Not in the type stubs; Django's default suffixes otherwise
                suffixes = getattr(
                    widget,
                    "widgets_names",
                    [f"_{index}" for index in range(len(widget.widgets))],
                )
                yield from (html_name + suffix for suffix in suffixes)
            else:
                yield html_name

    def _submitted_data(self, form: MontrekParameterForm) -> dict[str, list[str]]:
        """The submitted inputs of the form, to bind it again later. Lists, as
        an input may take several values."""
        data = self.request.GET
        return {
            name: data.getlist(name) for name in self._input_names(form) if name in data
        }

    @staticmethod
    def _values(form: MontrekParameterForm) -> dict[str, Any]:
        """The field values as submitted, or the initial ones of an unbound
        form."""
        return {name: form[name].value() for name in form.fields}

    def _drop_request_params(
        self, session_data: SessionDataType, form: MontrekParameterForm
    ) -> None:
        for name in self._input_names(form):
            session_data.pop(name, None)

    def _stored_for_path(self, field: str) -> dict[str, Any]:
        stored = self.request.session.get(field, {})
        return dict(stored.get(self.request.path, {}))

    def _store_for_path(self, field: str, stored_for_path: dict[str, Any]) -> None:
        stored = dict(self.request.session.get(field, {}))
        stored[self.request.path] = stored_for_path
        self.request.session[field] = stored
