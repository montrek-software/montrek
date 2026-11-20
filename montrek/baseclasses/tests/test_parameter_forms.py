import json

from django import forms
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory, TestCase

from baseclasses.forms import MontrekParameterForm
from baseclasses.parameter_forms import (
    SESSION_FIELD,
    SUBMITTED_FORM_PARAM,
    ParameterForms,
)

PATH = "/dummy/list"


class MockCurrencyForm(MontrekParameterForm):
    session_key = "currency"
    ccy_code = forms.ChoiceField(
        choices=[("CHF", "CHF"), ("EUR", "EUR"), ("USD", "USD")], initial="CHF"
    )


class MockOptionsForm(MontrekParameterForm):
    session_key = "options"
    with_closed = forms.BooleanField(required=False, initial=True)
    as_of = forms.SplitDateTimeField(required=False)


class MockColumnsForm(MontrekParameterForm):
    session_key = "columns"
    shown = forms.MultipleChoiceField(
        choices=[("a", "A"), ("b", "B"), ("c", "C")], initial=["a"]
    )


class TestParameterForms(TestCase):
    def setUp(self):
        self.session = SessionStore()

    def request(self, path: str = PATH, **params):
        request = RequestFactory().get(path, params)
        request.session = self.session
        return request

    def submit(self, path: str = PATH, **params):
        return self.request(path, **{SUBMITTED_FORM_PARAM: "currency", **params})

    def apply(self, request, form_classes=(MockCurrencyForm,), persist=True):
        parameter_forms = ParameterForms(form_classes, request, persist=persist)
        session_data = parameter_forms.update_session_data(dict(request.GET))
        return parameter_forms, session_data

    def test_initial_values_apply_without_a_submission(self):
        parameter_forms, session_data = self.apply(self.request())

        self.assertEqual(session_data["currency"], {"ccy_code": "CHF"})
        (form,) = parameter_forms.forms
        self.assertFalse(form.is_bound)

    def test_submitted_values_apply_and_are_kept_for_the_page(self):
        _, session_data = self.apply(self.submit(**{"currency-ccy_code": "USD"}))
        self.assertEqual(session_data["currency"], {"ccy_code": "USD"})

        _, session_data = self.apply(self.request())
        self.assertEqual(session_data["currency"], {"ccy_code": "USD"})

    def test_request_params_of_the_form_are_not_left_in_the_session_data(self):
        _, session_data = self.apply(self.submit(**{"currency-ccy_code": "USD"}))

        self.assertNotIn("currency-ccy_code", session_data)
        self.assertNotIn(SUBMITTED_FORM_PARAM, session_data)

    def test_invalid_submission_shows_errors_and_keeps_the_previous_value(self):
        self.apply(self.submit(**{"currency-ccy_code": "USD"}))

        parameter_forms, session_data = self.apply(
            self.submit(**{"currency-ccy_code": "XXX"})
        )

        self.assertEqual(session_data["currency"], {"ccy_code": "USD"})
        (form,) = parameter_forms.forms
        self.assertIn("ccy_code", form.errors)
        _, session_data = self.apply(self.request())
        self.assertEqual(session_data["currency"], {"ccy_code": "USD"})

    def test_stored_values_that_no_longer_validate_fall_back_to_the_initial(self):
        self.session[SESSION_FIELD] = {
            PATH: {"currency": {"currency-ccy_code": ["GBP"]}}
        }

        parameter_forms, session_data = self.apply(self.request())

        self.assertEqual(session_data["currency"], {"ccy_code": "CHF"})
        self.assertFalse(parameter_forms.forms[0].errors)

    def test_values_are_kept_per_page(self):
        self.apply(self.submit(**{"currency-ccy_code": "USD"}))

        _, session_data = self.apply(self.request("/other/list"))

        self.assertEqual(session_data["currency"], {"ccy_code": "CHF"})

    def test_without_persist_the_session_is_not_written(self):
        self.apply(self.submit(**{"currency-ccy_code": "USD"}), persist=False)

        self.assertNotIn(SESSION_FIELD, self.session)

    def test_a_submission_of_another_form_leaves_this_one(self):
        self.apply(self.submit(**{"currency-ccy_code": "USD"}))

        _, session_data = self.apply(
            self.request(**{SUBMITTED_FORM_PARAM: "columns", "columns-shown": "b"}),
            form_classes=(MockCurrencyForm, MockColumnsForm),
        )

        self.assertEqual(session_data["currency"], {"ccy_code": "USD"})
        self.assertEqual(session_data["columns"], {"shown": ["b"]})

    def test_a_field_with_several_values_is_kept(self):
        request = RequestFactory().get(
            PATH, {SUBMITTED_FORM_PARAM: "columns", "columns-shown": ["a", "c"]}
        )
        request.session = self.session
        self.apply(request, form_classes=(MockColumnsForm,))

        _, session_data = self.apply(self.request(), form_classes=(MockColumnsForm,))

        self.assertEqual(session_data["columns"], {"shown": ["a", "c"]})

    def test_values_are_serialisable(self):
        """Download tasks take the session data as JSON."""
        _, session_data = self.apply(self.submit(**{"currency-ccy_code": "USD"}))

        self.assertEqual(
            json.loads(json.dumps(session_data["currency"])), {"ccy_code": "USD"}
        )

    def test_an_unchecked_box_is_kept(self):
        """An unchecked box submits nothing, which is a valid submission."""
        options = (MockOptionsForm,)
        self.apply(self.request(**{SUBMITTED_FORM_PARAM: "options"}), options)

        _, session_data = self.apply(self.request(), options)

        self.assertFalse(session_data["options"]["with_closed"])

    def test_a_field_of_several_widgets_is_kept(self):
        options = (MockOptionsForm,)
        inputs = {"options-as_of_0": "2026-11-20", "options-as_of_1": "16:30"}
        _, session_data = self.apply(
            self.request(**{SUBMITTED_FORM_PARAM: "options"}, **inputs), options
        )
        for name in inputs:
            self.assertNotIn(name, session_data)

        _, session_data = self.apply(self.request(), options)

        self.assertEqual(session_data["options"]["as_of"], ["2026-11-20", "16:30"])

    def test_applied_values_are_stored_for_other_views(self):
        self.apply(self.submit(**{"currency-ccy_code": "USD"}))

        self.assertEqual(
            ParameterForms.stored_values(dict(self.session), PATH),
            {"currency": {"ccy_code": "USD"}},
        )
        self.assertEqual(ParameterForms.stored_values(dict(self.session), "/other"), {})

    def test_initial_values_are_not_stored(self):
        """They may be of any type, while the session takes JSON only."""
        self.apply(self.request())

        self.assertEqual(ParameterForms.stored_values(dict(self.session), PATH), {})

    def test_without_forms_nothing_changes(self):
        parameter_forms, session_data = self.apply(self.request(), form_classes=())

        self.assertEqual(parameter_forms.forms, [])
        self.assertEqual(session_data, {})
        self.assertNotIn(SESSION_FIELD, self.session)
