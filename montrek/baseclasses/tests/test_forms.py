from django.contrib.admin.widgets import FilteredSelectMultiple
from django.db.models import QuerySet
from django.forms import CheckboxSelectMultiple
from django.test import TestCase

from baseclasses.forms import FilterForm, MontrekModelMultipleChoiceField


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
