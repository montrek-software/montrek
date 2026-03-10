from django import forms
from bs4 import BeautifulSoup
from django.template.loader import render_to_string
from django.test import TestCase


class _TextForm(forms.Form):
    text_field = forms.CharField(label="Text Field")


class _CheckboxForm(forms.Form):
    bool_field = forms.BooleanField(label="Bool Field", required=False)


class _MultipleChoiceForm(forms.Form):
    choices_field = forms.MultipleChoiceField(
        label="Choices Field",
        choices=[("a", "Option A"), ("b", "Option B")],
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class _HelpTextForm(forms.Form):
    text_field = forms.CharField(label="Text Field", help_text="Some help text")


class TestFormFieldsTemplate(TestCase):
    """Tests for baseclasses/templates/includes/_form_fields.html."""

    TEMPLATE = "includes/_form_fields.html"

    def _render(self, form: forms.Form) -> BeautifulSoup:
        html = render_to_string(self.TEMPLATE, {"form": form})
        return BeautifulSoup(html, "html.parser")

    # ------------------------------------------------------------------
    # Column-size tests (col-lg-3 / col-lg-9)
    # ------------------------------------------------------------------

    def test_regular_field_uses_col_lg_3_label(self):
        soup = self._render(_TextForm())
        label = soup.find("label", class_="col-lg-3")
        self.assertIsNotNone(label)

    def test_regular_field_uses_col_lg_9_input(self):
        soup = self._render(_TextForm())
        div = soup.find("div", class_="col-lg-9")
        self.assertIsNotNone(div)

    def test_checkbox_field_uses_col_lg_3(self):
        soup = self._render(_CheckboxForm())
        div = soup.find("div", class_="col-lg-3")
        self.assertIsNotNone(div)

    def test_checkbox_field_uses_col_lg_9(self):
        soup = self._render(_CheckboxForm())
        div = soup.find("div", class_="col-lg-9")
        self.assertIsNotNone(div)

    def test_multiple_choice_field_uses_col_lg_3_label(self):
        soup = self._render(_MultipleChoiceForm())
        label = soup.find("label", class_="col-lg-3")
        self.assertIsNotNone(label)

    def test_multiple_choice_field_uses_col_lg_9(self):
        soup = self._render(_MultipleChoiceForm())
        div = soup.find("div", class_="col-lg-9")
        self.assertIsNotNone(div)

    # ------------------------------------------------------------------
    # Branch-selection tests
    # ------------------------------------------------------------------

    def test_multiple_choice_renders_individual_choices(self):
        """CheckboxSelectMultiple must hit the allow_multiple_selected branch
        and render each choice as a separate form-check div."""
        soup = self._render(_MultipleChoiceForm())
        form_checks = soup.find_all("div", class_="form-check")
        self.assertEqual(len(form_checks), 2)

    def test_multiple_choice_uses_align_items_start(self):
        """Multi-choice uses align-items-start (not align-items-center)."""
        soup = self._render(_MultipleChoiceForm())
        row = soup.find("div", class_="align-items-start")
        self.assertIsNotNone(row)

    def test_single_checkbox_uses_align_items_center(self):
        """Single checkbox uses align-items-center."""
        soup = self._render(_CheckboxForm())
        row = soup.find("div", class_="align-items-center")
        self.assertIsNotNone(row)

    def test_single_checkbox_renders_form_check_wrapper(self):
        """Single checkbox is wrapped in a form-check div."""
        soup = self._render(_CheckboxForm())
        form_check = soup.find("div", class_="form-check")
        self.assertIsNotNone(form_check)

    def test_regular_field_does_not_render_form_check(self):
        """Regular text field must not use the checkbox branch."""
        soup = self._render(_TextForm())
        self.assertIsNone(soup.find("div", class_="form-check"))

    # ------------------------------------------------------------------
    # Help-text tooltip
    # ------------------------------------------------------------------

    def test_help_text_renders_tooltip(self):
        soup = self._render(_HelpTextForm())
        tooltip = soup.find("span", attrs={"data-bs-toggle": "tooltip"})
        self.assertIsNotNone(tooltip)
        self.assertEqual(tooltip["data-bs-title"], "Some help text")

    # ------------------------------------------------------------------
    # word-break style on labels
    # ------------------------------------------------------------------

    def test_regular_field_label_has_word_break_style(self):
        soup = self._render(_TextForm())
        label = soup.find("label", style=lambda s: s and "word-break" in s)
        self.assertIsNotNone(label)

    def test_checkbox_label_has_word_break_style(self):
        soup = self._render(_CheckboxForm())
        label = soup.find("label", style=lambda s: s and "word-break" in s)
        self.assertIsNotNone(label)

    def test_multiple_choice_label_has_word_break_style(self):
        soup = self._render(_MultipleChoiceForm())
        label = soup.find("label", style=lambda s: s and "word-break" in s)
        self.assertIsNotNone(label)
