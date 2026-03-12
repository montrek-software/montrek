from django import forms
from django.test import SimpleTestCase

from baseclasses.templatetags.widget_tags import is_checkbox_select_multiple


class _CheckboxMultipleForm(forms.Form):
    field = forms.MultipleChoiceField(
        choices=[("a", "A"), ("b", "B")],
        widget=forms.CheckboxSelectMultiple,
    )


class _SelectMultipleForm(forms.Form):
    field = forms.MultipleChoiceField(
        choices=[("a", "A"), ("b", "B")],
        widget=forms.SelectMultiple,
    )


class _TextForm(forms.Form):
    field = forms.CharField()


class _ChoiceForm(forms.Form):
    field = forms.ChoiceField(choices=[("a", "A")])


class TestIsCheckboxSelectMultiple(SimpleTestCase):
    def test_returns_true_for_checkbox_select_multiple(self):
        form = _CheckboxMultipleForm()
        self.assertTrue(is_checkbox_select_multiple(form["field"]))

    def test_returns_false_for_select_multiple(self):
        form = _SelectMultipleForm()
        self.assertFalse(is_checkbox_select_multiple(form["field"]))

    def test_returns_false_for_text_input(self):
        form = _TextForm()
        self.assertFalse(is_checkbox_select_multiple(form["field"]))

    def test_returns_false_for_select(self):
        form = _ChoiceForm()
        self.assertFalse(is_checkbox_select_multiple(form["field"]))
