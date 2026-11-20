from typing import Any

from django.http import HttpRequest
from django.utils.datastructures import MultiValueDict

from baseclasses.forms import MontrekParameterForm
from baseclasses.typing import SessionDataType

# GET parameter naming the parameter form that was submitted
SUBMITTED_FORM_PARAM = "parameter_form"
# Session key of the submitted values, by request path and form
SESSION_FIELD = "parameter_forms"


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

    def update_session_data(self, session_data: SessionDataType) -> SessionDataType:
        stored = self._stored_for_path()
        for form_class in self.form_classes:
            key = form_class.session_key
            shown_form, applied_form = self._bind(form_class, stored.get(key))
            if self._is_submitted(form_class) and shown_form.is_valid():
                stored[key] = self._submitted_data(shown_form)
            self.forms.append(shown_form)
            session_data[key] = self._values(applied_form)
            self._drop_request_params(session_data, shown_form)
        session_data.pop(SUBMITTED_FORM_PARAM, None)
        if self.persist and self.form_classes:
            self._store_for_path(stored)
        return session_data

    def _bind(
        self, form_class: type[MontrekParameterForm], stored_data: dict | None
    ) -> tuple[MontrekParameterForm, MontrekParameterForm]:
        """The form to show and the form whose values apply."""
        prefix = form_class.session_key
        previous = (
            form_class(MultiValueDict(stored_data), prefix=prefix)
            if stored_data
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

    def _submitted_data(self, form: MontrekParameterForm) -> dict[str, list[str]]:
        """The submitted values of the form's fields, to bind it again later.
        Lists, as a field may take several values."""
        data = self.request.GET
        names = [form.add_prefix(name) for name in form.fields]
        return {name: data.getlist(name) for name in names if name in data}

    @staticmethod
    def _values(form: MontrekParameterForm) -> dict[str, Any]:
        """The field values as submitted, or the initial ones of an unbound
        form, which keeps the session data serialisable."""
        return {name: form[name].value() for name in form.fields}

    @staticmethod
    def _drop_request_params(
        session_data: SessionDataType, form: MontrekParameterForm
    ) -> None:
        for name in form.fields:
            session_data.pop(form.add_prefix(name), None)

    def _stored_for_path(self) -> dict[str, dict]:
        stored = self.request.session.get(SESSION_FIELD, {})
        return dict(stored.get(self.request.path, {}))

    def _store_for_path(self, stored_for_path: dict[str, dict]) -> None:
        stored = dict(self.request.session.get(SESSION_FIELD, {}))
        stored[self.request.path] = stored_for_path
        self.request.session[SESSION_FIELD] = stored
