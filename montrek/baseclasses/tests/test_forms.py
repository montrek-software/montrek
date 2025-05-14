from django.contrib.admin.widgets import FilteredSelectMultiple
from django.db.models import QuerySet
from django.forms import CheckboxSelectMultiple, forms
from django.test import TestCase

from baseclasses.forms import (
    BaseMontrekChoiceField,
    FilterForm,
    MontrekModelCharChoiceField,
    MontrekModelMultipleChoiceField,
)


class TestFilterForm(TestCase):
    def test_filter_form(self):
        form = FilterForm(filter_field_choices=[("field1", "Field 1")])

        self.assertTrue(form.fields["filter_field"].initial == "")
        self.assertTrue(form.fields["filter_lookup"].initial == "exact")
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
        self.assertEqual(form.fields["filter_lookup"].initial, "exact")
        self.assertFalse(form.fields["filter_negate"].initial)
        self.assertFalse(form.fields["filter_value"].initial)


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
        self.assertRaises(forms.ValidationError, test_field.clean, None)

    def test_get_initial_link(self):
        test_field = MontrekModelCharChoiceField(
            display_field="abc",
        )
        self.assertEqual(
            test_field.get_initial_link({"abc": "def"}, [], "abc", ","), "def"
        )
