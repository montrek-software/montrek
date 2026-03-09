from django.contrib.admin.widgets import FilteredSelectMultiple
from django.db.models import QuerySet, DateField
from django.forms import (
    CheckboxSelectMultiple,
    PasswordInput,
    DateInput,
    ValidationError,
)
from django.test import TestCase
from encrypted_fields import EncryptedCharField

from baseclasses.forms import (
    BaseMontrekChoiceField,
    FilterForm,
    MontrekCreateForm,
    MontrekModelCharChoiceField,
    MontrekModelMultipleChoiceField,
)


class TestFilterForm(TestCase):
    def test_filter_form(self):
        form = FilterForm(filter_field_choices=[("field1", "Field 1")])

        self.assertTrue(form.fields["filter_field"].initial == "")
        self.assertTrue(form.fields["filter_lookup"].initial == "iexact")
        self.assertFalse(form.fields["filter_negate"].initial)
        self.assertTrue(form.fields["filter_value"].initial == "")

        self.assertTrue(form.fields["filter_field"].choices == [("field1", "Field 1")])
        self.assertEqual(
            form.fields["filter_negate"].choices, [(False, ""), (True, "not")]
        )
        self.assertTrue(
            form.fields["filter_lookup"].choices == form.LookupChoices.choices
        )

    def test_filter_form_filter(self):
        form = FilterForm(
            filter={
                "field1__in": {
                    "filter_negate": True,
                    "filter_value": ["value1", "value2"],
                }
            }
        )

        self.assertTrue(form.fields["filter_field"].initial == "field1")
        self.assertTrue(form.fields["filter_lookup"].initial == "in")
        self.assertTrue(form.fields["filter_negate"].initial)
        self.assertTrue(form.fields["filter_value"].initial == "value1,value2")

    def test_filter_form_or(self):
        form = FilterForm(filter={"or": {"field1__in": {"filter_value": ["value1"]}}})
        self.assertFalse(form.fields["filter_field"].initial)
        self.assertEqual(form.fields["filter_lookup"].initial, "iexact")
        self.assertFalse(form.fields["filter_negate"].initial)
        self.assertFalse(form.fields["filter_value"].initial)


class MockHubClass: ...


class MockRepository:
    hub_class = MockHubClass
    display_field_names = {"field_date": "Field Date"}
    field_help_texts = {"field_date": "Help Field Date"}

    def std_satellite_fields(self):
        return [
            EncryptedCharField(name="encrypted_field"),
            DateField(name="field_date"),
        ]


class MockCreateForm(MontrekCreateForm):
    field_order = ["field_a", "field_b"]


class _TestableCreateForm(MontrekCreateForm):
    """Skip model-level unique validation so clean() can be tested in isolation."""

    def _validate_unique(self):
        pass


class TestMontrekCreateForm(TestCase):
    def test_special_widgets(self):
        test_form = MontrekCreateForm(repository=MockRepository())
        fields = test_form.fields
        self.assertIsInstance(fields["encrypted_field"].widget, PasswordInput)
        self.assertIsInstance(fields["field_date"].widget, DateInput)

    def test_rename_field(self):
        test_form = MontrekCreateForm(repository=MockRepository())
        fields = test_form.fields
        self.assertEqual(fields["field_date"].label, "Field Date")

    def test_field_order(self):
        test_form = MockCreateForm(repository=MockRepository())
        test_form.set_field_order()
        self.assertEqual(test_form.field_order, ["field_a", "field_b", "hub_entity_id"])

    def test_field_help_texts(self):
        test_form = MontrekCreateForm(repository=MockRepository())
        fields = test_form.fields
        self.assertEqual(fields["field_date"].help_text, "Help Field Date")


class TestEncryptedFieldBehaviour(TestCase):
    """Tests for the security fix on EncryptedCharField in MontrekCreateForm.

    Verifies that:
    - render_value is False (value never appears in HTML)
    - required is preserved on create, relaxed on update
    - clean() restores the existing value when the field is left blank on update
    """

    # ------------------------------------------------------------------
    # Widget / required attribute tests
    # ------------------------------------------------------------------

    def test_encrypted_widget_does_not_render_value(self):
        """render_value must be False so the secret never appears in the HTML."""
        form = MontrekCreateForm(repository=MockRepository())
        self.assertFalse(form.fields["encrypted_field"].widget.render_value)

    def test_encrypted_field_required_on_create(self):
        """On create (no initial data) the field keeps its default required=True."""
        form = MontrekCreateForm(repository=MockRepository())
        self.assertTrue(form.fields["encrypted_field"].required)

    def test_encrypted_field_not_required_on_update(self):
        """On update (initial value present) required is set to False so a blank
        submission is valid and clean() can restore the existing value."""
        form = MontrekCreateForm(
            repository=MockRepository(),
            initial={"encrypted_field": "existing_secret"},
        )
        self.assertFalse(form.fields["encrypted_field"].required)

    def test_non_encrypted_field_required_unaffected(self):
        """Other field types are not touched by the encrypted-field logic."""
        form_create = MontrekCreateForm(repository=MockRepository())
        form_update = MontrekCreateForm(
            repository=MockRepository(),
            initial={"encrypted_field": "existing_secret"},
        )
        self.assertEqual(
            form_create.fields["field_date"].required,
            form_update.fields["field_date"].required,
        )

    # ------------------------------------------------------------------
    # clean() behaviour tests
    # ------------------------------------------------------------------

    def _make_form(self, initial=None, submitted=None):
        """Return a _TestableCreateForm with cleaned_data pre-set for direct
        clean() testing (bypasses full ModelForm validation chain)."""
        form = _TestableCreateForm(
            repository=MockRepository(),
            initial=initial or {},
        )
        form.cleaned_data = submitted or {}
        return form

    def test_clean_restores_initial_value_when_blank_on_update(self):
        """If an encrypted field is submitted blank on update, clean() fills it
        back from the initial data so the manager receives the existing value."""
        form = self._make_form(
            initial={"encrypted_field": "existing_secret"},
            submitted={"encrypted_field": ""},
        )
        result = form.clean()
        self.assertEqual(result["encrypted_field"], "existing_secret")

    def test_clean_keeps_new_value_when_provided_on_update(self):
        """If the user actually types a new secret, clean() preserves it."""
        form = self._make_form(
            initial={"encrypted_field": "existing_secret"},
            submitted={"encrypted_field": "new_secret"},
        )
        result = form.clean()
        self.assertEqual(result["encrypted_field"], "new_secret")

    def test_clean_leaves_blank_on_create_when_no_initial(self):
        """On create there is no initial value, so a blank submission stays blank
        (the manager / model field validation handles the required check)."""
        form = self._make_form(
            initial={},
            submitted={"encrypted_field": ""},
        )
        result = form.clean()
        self.assertEqual(result["encrypted_field"], "")

    def test_clean_does_not_restore_none_initial(self):
        """If the initial value is None (field was never set), clean() must not
        substitute it — returning None would be worse than an empty string."""
        form = self._make_form(
            initial={"encrypted_field": None},
            submitted={"encrypted_field": ""},
        )
        result = form.clean()
        self.assertEqual(result["encrypted_field"], "")


class TestMontrekModelMultipleChoiceField(TestCase):
    def test_init__widget(self):
        field_kwargs = {"display_field": "field1", "queryset": QuerySet()}
        checkbox_field = MontrekModelMultipleChoiceField(
            **field_kwargs, use_checkboxes_for_many_to_many=True
        )
        list_field = MontrekModelMultipleChoiceField(
            **field_kwargs, use_checkboxes_for_many_to_many=False
        )
        self.assertTrue(isinstance(checkbox_field.widget, CheckboxSelectMultiple))
        self.assertTrue(isinstance(list_field.widget, FilteredSelectMultiple))
        self.assertEqual(list_field.widget.verbose_name, "field1")

    def test_init__widget_css_classes(self):
        field_kwargs = {"display_field": "field1", "queryset": QuerySet()}
        checkbox_field = MontrekModelMultipleChoiceField(
            **field_kwargs, use_checkboxes_for_many_to_many=True
        )
        list_field = MontrekModelMultipleChoiceField(
            **field_kwargs, use_checkboxes_for_many_to_many=False
        )
        self.assertNotIn("form-select", checkbox_field.widget.attrs.get("class", ""))
        self.assertIn("form-select", list_field.widget.attrs.get("class", ""))


class TestBaseMontrekChoiceField(TestCase):
    def test_init__widget(self):
        field_kwargs = {"display_field": "field1", "queryset": QuerySet()}
        checkbox_field = MontrekModelMultipleChoiceField(
            **field_kwargs, use_checkboxes_for_many_to_many=True
        )
        list_field = MontrekModelMultipleChoiceField(
            **field_kwargs, use_checkboxes_for_many_to_many=False
        )
        self.assertTrue(isinstance(checkbox_field.widget, CheckboxSelectMultiple))
        self.assertTrue(isinstance(list_field.widget, FilteredSelectMultiple))

    def test_get_initial_link_not_implemented(self):
        field = BaseMontrekChoiceField(display_field="field1")
        with self.assertRaises(NotImplementedError):
            field.get_initial_link(None, None, None, None)


class TestMontrekModelCharChoiceField(TestCase):
    def test_raise_error_when_empty(self):
        test_field = MontrekModelCharChoiceField(display_field="abc")
        self.assertRaises(ValidationError, test_field.clean, None)

    def test_get_initial_link(self):
        test_field = MontrekModelCharChoiceField(
            display_field="abc",
        )
        self.assertEqual(
            test_field.get_initial_link({"abc": "def"}, [], "abc", ","), "def"
        )
