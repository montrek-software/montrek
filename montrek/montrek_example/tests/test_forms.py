import json
from decimal import Decimal

import pandas as pd
from django import forms
from django.forms import PasswordInput
from django.test import TestCase, override_settings

from baseclasses.forms import (
    DateRangeForm,
    FilterForm,
    GermanDecimalFormField,
    GermanFloatFormField,
    MontrekCreateForm,
    MontrekModelCharChoiceField,
    MontrekModelChoiceField,
    MontrekModelMultipleChoiceField,
)
from montrek.utils import SystemFormatting
from montrek_example.forms import (
    ExampleABaseForm,
    ExampleACreateForm,
    ExampleBCreateForm,
    ExampleCCreateForm,
)
from montrek_example.repositories.hub_a_repository import (
    HubARepository,
    HubARepository5,
)
from montrek_example.repositories.hub_b_repository import HubBRepository
from montrek_example.repositories.hub_c_repository import (
    HubCBooleanRepository,
    HubCRepositoryOnlyStatic,
)
from montrek_example.repositories.hub_d_repository import HubDRepository
from montrek_example.repositories.hub_e_repository import HubERepository
from montrek_example.tests.factories.montrek_example_factories import (
    SatB1Factory,
    SatC1Factory,
)


# ---------------------------------------------------------------------------
# Test-only form helpers
# ---------------------------------------------------------------------------


class _HubBBaseForm(MontrekCreateForm): ...


class _HubBCheckboxForm(MontrekCreateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_link_choice_field(
            display_field="field_d1_str",
            link_name="link_hub_b_hub_d",
            queryset=self.repository.get_hub_d_objects(),
            use_checkboxes_for_many_to_many=True,
        )


class _HubCBooleanForm(MontrekCreateForm): ...


class _HubARepositoryWithHelpTexts(HubARepository):
    field_help_texts = {
        "field_a1_str": "Help for satellite field",
        "link_hub_a_hub_b": "Help for link field",
    }


# ---------------------------------------------------------------------------
# GermanDecimalFormField
# ---------------------------------------------------------------------------


class TestGermanDecimalFormField(TestCase):
    def test_german_notation_converts_comma(self):
        field = GermanDecimalFormField()
        result = field.to_python("1.234,56")
        self.assertEqual(result, Decimal("1234.56"))

    def test_standard_notation_passthrough(self):
        field = GermanDecimalFormField()
        result = field.to_python("1234.56")
        self.assertEqual(result, Decimal("1234.56"))

    def test_no_comma_value_unchanged(self):
        field = GermanDecimalFormField()
        result = field.to_python("42")
        self.assertEqual(result, Decimal("42"))

    def test_uses_text_input_widget(self):
        field = GermanDecimalFormField()
        self.assertIsInstance(field.widget, forms.TextInput)


# ---------------------------------------------------------------------------
# GermanFloatFormField
# ---------------------------------------------------------------------------


class TestGermanFloatFormField(TestCase):
    def test_german_notation_converts_comma(self):
        field = GermanFloatFormField()
        result = field.to_python("1.234,56")
        self.assertAlmostEqual(result, 1234.56)

    def test_standard_notation_passthrough(self):
        field = GermanFloatFormField()
        result = field.to_python("1234.56")
        self.assertAlmostEqual(result, 1234.56)

    def test_no_comma_passthrough(self):
        field = GermanFloatFormField()
        result = field.to_python("42")
        self.assertEqual(result, 42.0)

    def test_uses_text_input_widget(self):
        field = GermanFloatFormField()
        self.assertIsInstance(field.widget, forms.TextInput)


# ---------------------------------------------------------------------------
# DateRangeForm
# ---------------------------------------------------------------------------


class TestDateRangeForm(TestCase):
    def test_fields_present(self):
        form = DateRangeForm()
        self.assertIn("start_date", form.fields)
        self.assertIn("end_date", form.fields)

    def test_valid_data(self):
        form = DateRangeForm(
            data={"start_date": "2024-01-01", "end_date": "2024-12-31"}
        )
        self.assertTrue(form.is_valid())

    def test_invalid_start_date(self):
        form = DateRangeForm(
            data={"start_date": "not-a-date", "end_date": "2024-12-31"}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("start_date", form.errors)


# ---------------------------------------------------------------------------
# FilterForm
# ---------------------------------------------------------------------------


class TestFilterForm(TestCase):
    def test_no_args_creates_empty_form(self):
        form = FilterForm()
        self.assertIn("filter_field", form.fields)
        self.assertIn("filter_negate", form.fields)
        self.assertIn("filter_lookup", form.fields)
        self.assertIn("filter_value", form.fields)

    def test_with_filter_field_choices(self):
        choices = [("name", "Name"), ("code", "Code")]
        form = FilterForm(filter_field_choices=choices)
        self.assertEqual(form.fields["filter_field"].choices, choices)

    def test_filter_with_double_underscore_key(self):
        filter_data = {
            "field_name__contains": {"filter_negate": False, "filter_value": "test"}
        }
        form = FilterForm(filter=filter_data)
        self.assertEqual(form.fields["filter_field"].initial, "field_name")
        self.assertEqual(form.fields["filter_lookup"].initial, "contains")
        self.assertEqual(form.fields["filter_value"].initial, "test")

    def test_filter_with_simple_key_defaults_lookup_to_exact(self):
        filter_data = {"field_name": {"filter_negate": False, "filter_value": "abc"}}
        form = FilterForm(filter=filter_data)
        self.assertEqual(form.fields["filter_field"].initial, "field_name")
        self.assertEqual(form.fields["filter_lookup"].initial, "exact")

    def test_filter_or_key_resets_to_defaults(self):
        filter_data = {"OR": {"filter_negate": True, "filter_value": "x"}}
        form = FilterForm(filter=filter_data)
        self.assertEqual(form.fields["filter_field"].initial, "")
        self.assertEqual(form.fields["filter_value"].initial, "")

    def test_filter_index_out_of_bounds_resets_to_defaults(self):
        filter_data = {
            "field_name__iexact": {"filter_negate": False, "filter_value": "v"}
        }
        form = FilterForm(filter=filter_data, filter_index=99)
        self.assertEqual(form.fields["filter_field"].initial, "")

    def test_filter_list_value_joined_with_comma(self):
        filter_data = {
            "field_name__in": {"filter_negate": False, "filter_value": [1, 2, 3]}
        }
        form = FilterForm(filter=filter_data)
        self.assertEqual(form.fields["filter_value"].initial, "1,2,3")

    def test_filter_negate_is_set(self):
        filter_data = {"field__iexact": {"filter_negate": True, "filter_value": "v"}}
        form = FilterForm(filter=filter_data)
        self.assertTrue(form.fields["filter_negate"].initial)

    def test_filter_with_none_filter_resets_to_defaults(self):
        form = FilterForm(filter=None)
        self.assertEqual(form.fields["filter_field"].initial, "")

    def test_filter_with_non_dict_resets_to_defaults(self):
        form = FilterForm(filter="not_a_dict")
        self.assertEqual(form.fields["filter_field"].initial, "")

    def test_lookup_choices_present(self):
        choices_values = [c[0] for c in FilterForm.LookupChoices.choices]
        self.assertIn("contains", choices_values)
        self.assertIn("exact", choices_values)
        self.assertIn("isnull", choices_values)


# ---------------------------------------------------------------------------
# MontrekCreateForm — initialization and satellite fields
# ---------------------------------------------------------------------------


class TestMontrekCreateFormInit(TestCase):
    def test_no_repository_raises_value_error(self):
        with self.assertRaises(ValueError):
            ExampleABaseForm()

    def test_satellite_fields_added(self):
        repo = HubARepository({})
        form = ExampleABaseForm(repository=repo)
        self.assertIn("field_a1_str", form.fields)
        self.assertIn("field_a1_int", form.fields)
        self.assertIn("field_a2_str", form.fields)
        self.assertIn("field_a2_float", form.fields)

    def test_hub_entity_id_always_present_and_readonly(self):
        repo = HubARepository({})
        form = ExampleABaseForm(repository=repo)
        self.assertIn("hub_entity_id", form.fields)
        self.assertTrue(form.fields["hub_entity_id"].widget.attrs.get("readonly"))

    def test_date_field_uses_date_input_widget(self):
        repo = HubBRepository({})
        form = _HubBBaseForm(repository=repo)
        widget = form.fields["field_b1_date"].widget
        self.assertIsInstance(widget, forms.DateInput)
        # Django's Input.__init__ pops 'type' from attrs into input_type
        self.assertEqual(widget.input_type, "date")

    @override_settings(NUMBER_FORMATTING=SystemFormatting.DE)
    def test_float_field_uses_german_form_field_with_de_setting(self):
        repo = HubARepository({})
        form = ExampleABaseForm(repository=repo)
        self.assertIsInstance(form.fields["field_a2_float"], GermanFloatFormField)

    def test_float_field_uses_standard_form_field_without_de_setting(self):
        repo = HubARepository({})
        form = ExampleABaseForm(repository=repo)
        self.assertNotIsInstance(form.fields["field_a2_float"], GermanFloatFormField)

    def test_display_field_names_applied_to_satellite_field(self):
        repo = HubARepository({})
        form = ExampleACreateForm(repository=repo)
        self.assertEqual(form.fields["field_a2_float"].label, "Renamed Label")

    def test_display_field_names_applied_to_link_field(self):
        repo = HubARepository({})
        form = ExampleACreateForm(repository=repo)
        self.assertEqual(form.fields["link_hub_a_hub_c"].label, "Renamed Link Label")

    def test_field_help_text_applied_to_satellite_field(self):
        repo = _HubARepositoryWithHelpTexts({})
        form = ExampleACreateForm(repository=repo)
        self.assertEqual(
            form.fields["field_a1_str"].help_text, "Help for satellite field"
        )

    def test_field_help_text_applied_to_link_field(self):
        repo = _HubARepositoryWithHelpTexts({})
        form = ExampleACreateForm(repository=repo)
        self.assertEqual(
            form.fields["link_hub_a_hub_b"].help_text, "Help for link field"
        )

    def test_encrypted_field_uses_password_input(self):
        repo = HubARepository5({})
        form = ExampleABaseForm(repository=repo)
        self.assertIsInstance(form.fields["secret_field"].widget, PasswordInput)


# ---------------------------------------------------------------------------
# Bootstrap styling via _apply_bootstrap_classes
# ---------------------------------------------------------------------------


class TestBootstrapStyling(TestCase):
    def test_checkbox_input_gets_form_check_input(self):
        repo = HubCBooleanRepository({})
        form = _HubCBooleanForm(repository=repo)
        self.assertEqual(
            form.fields["field_bool_1"].widget.attrs.get("class"), "form-check-input"
        )

    def test_select_gets_form_select(self):
        repo = HubBRepository({})
        form = _HubBBaseForm(repository=repo)
        self.assertEqual(
            form.fields["field_b2_choice"].widget.attrs.get("class"), "form-select"
        )

    def test_date_input_gets_form_control_w_auto(self):
        repo = HubBRepository({})
        form = _HubBBaseForm(repository=repo)
        self.assertEqual(
            form.fields["field_b1_date"].widget.attrs.get("class"),
            "form-control w-auto",
        )

    def test_text_input_gets_form_control(self):
        repo = HubARepository({})
        form = ExampleABaseForm(repository=repo)
        self.assertEqual(
            form.fields["field_a1_str"].widget.attrs.get("class"), "form-control"
        )

    def test_readonly_field_appends_form_control_plaintext(self):
        # hub_entity_id is added by _add_hub_entity_id_field before
        # _apply_bootstrap_classes runs, so it exercises the readonly branch.
        repo = HubARepository({})
        form = ExampleABaseForm(repository=repo)
        css_class = form.fields["hub_entity_id"].widget.attrs.get("class", "")
        self.assertIn("form-control-plaintext", css_class)

    def test_checkbox_select_multiple_not_styled_as_form_select(self):
        repo = HubBRepository({})
        form = _HubBCheckboxForm(repository=repo)
        css_class = form.fields["link_hub_b_hub_d"].widget.attrs.get("class", "")
        self.assertNotIn("form-select", css_class)

    def test_textarea_gets_form_control_resizable(self):
        repo = HubARepository({})
        form = ExampleABaseForm(repository=repo)
        form.fields["notes"] = forms.CharField(widget=forms.Textarea())
        form._apply_bootstrap_classes()
        self.assertEqual(
            form.fields["notes"].widget.attrs.get("class"), "form-control resizable"
        )

    def test_id_attr_set_for_all_fields(self):
        repo = HubARepository({})
        form = ExampleABaseForm(repository=repo)
        for name, field in form.fields.items():
            self.assertEqual(
                field.widget.attrs.get("id"), f"id_{name}", msg=f"Missing id for {name}"
            )


# ---------------------------------------------------------------------------
# set_field_order
# ---------------------------------------------------------------------------


class TestSetFieldOrder(TestCase):
    def test_hub_entity_id_appended_to_existing_field_order(self):
        repo = HubCRepositoryOnlyStatic({})
        form = ExampleCCreateForm(repository=repo)
        form.set_field_order()
        self.assertEqual(form.field_order[-1], "hub_entity_id")
        self.assertIn("field_c1_str", form.field_order)

    def test_hub_entity_id_not_duplicated_if_already_in_order(self):
        repo = HubCRepositoryOnlyStatic({})
        form = ExampleCCreateForm(repository=repo)
        form.field_order = ["field_c1_str", "hub_entity_id"]
        form.set_field_order()
        self.assertEqual(form.field_order.count("hub_entity_id"), 1)

    def test_set_field_order_without_class_level_field_order(self):
        repo = HubARepository({})
        form = ExampleABaseForm(repository=repo)
        form.set_field_order()
        self.assertEqual(form.field_order[-1], "hub_entity_id")
        for name in form.fields:
            if name != "hub_entity_id":
                self.assertIn(name, form.field_order)


# ---------------------------------------------------------------------------
# add_link_choice_field
# ---------------------------------------------------------------------------


class TestAddLinkChoiceField(TestCase):
    def test_many_to_many_creates_multiple_choice_field(self):
        repo = HubBRepository({})
        form = ExampleBCreateForm(repository=repo)
        self.assertIsInstance(
            form.fields["link_hub_b_hub_d"], MontrekModelMultipleChoiceField
        )

    def test_many_to_many_with_checkboxes_uses_checkbox_widget(self):
        repo = HubBRepository({})
        form = _HubBCheckboxForm(repository=repo)
        self.assertIsInstance(
            form.fields["link_hub_b_hub_d"].widget, forms.CheckboxSelectMultiple
        )

    def test_non_m2m_creates_model_choice_field(self):
        repo = HubARepository({})
        form = ExampleACreateForm(repository=repo)
        self.assertIsInstance(form.fields["link_hub_a_hub_b"], MontrekModelChoiceField)

    def test_char_field_creates_char_choice_field(self):
        repo = HubARepository({})
        form = ExampleACreateForm(repository=repo)
        self.assertIsInstance(
            form.fields["link_hub_a_hub_c"], MontrekModelCharChoiceField
        )

    def test_readonly_adds_text_input_with_readonly_attr(self):
        repo = HubARepository({})
        form = ExampleACreateForm(repository=repo)
        self.assertEqual(
            form.fields["link_hub_a_hub_b"].widget.attrs.get("readonly"), "readonly"
        )

    def test_display_name_applied_to_link_field(self):
        repo = HubARepository({})
        form = ExampleACreateForm(repository=repo)
        self.assertEqual(form.fields["link_hub_a_hub_c"].label, "Renamed Link Label")

    def test_help_text_applied_to_link_field(self):
        repo = _HubARepositoryWithHelpTexts({})
        form = ExampleACreateForm(repository=repo)
        self.assertEqual(
            form.fields["link_hub_a_hub_b"].help_text, "Help for link field"
        )


# ---------------------------------------------------------------------------
# clean() with encrypted fields
# ---------------------------------------------------------------------------


class TestCleanEncryptedField(TestCase):
    def test_clean_keeps_initial_encrypted_value_when_submitted_empty(self):
        repo = HubARepository5({})
        form = ExampleABaseForm(
            initial={"secret_field": "existing_secret"},
            data={"field_a5_str": "test", "hub_entity_id": ""},
            repository=repo,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["secret_field"], "existing_secret")

    def test_clean_uses_newly_submitted_encrypted_value(self):
        repo = HubARepository5({})
        form = ExampleABaseForm(
            initial={"secret_field": "old_secret"},
            data={
                "field_a5_str": "test",
                "hub_entity_id": "",
                "secret_field": "new_secret",
            },
            repository=repo,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["secret_field"], "new_secret")

    def test_encrypted_field_not_required_when_initial_is_set(self):
        repo = HubARepository5({})
        form = ExampleABaseForm(
            initial={"secret_field": "existing"},
            repository=repo,
        )
        self.assertFalse(form.fields["secret_field"].required)


# ---------------------------------------------------------------------------
# BaseMontrekChoiceField.label_from_instance
# ---------------------------------------------------------------------------


class TestLabelFromInstance(TestCase):
    def test_returns_display_field_attribute(self):
        SatC1Factory(field_c1_str="display_value")
        queryset = HubCRepositoryOnlyStatic().receive()
        field = MontrekModelChoiceField(display_field="field_c1_str", queryset=queryset)
        obj = queryset.first()
        result = field.label_from_instance(obj)
        self.assertEqual(result, obj.field_c1_str)

    def test_bootstrap_form_select_class_applied(self):
        queryset = HubCRepositoryOnlyStatic().receive()
        field = MontrekModelChoiceField(display_field="field_c1_str", queryset=queryset)
        self.assertIn("form-select", field.widget.attrs.get("class", ""))


# ---------------------------------------------------------------------------
# MontrekModelChoiceField.get_initial_link
# ---------------------------------------------------------------------------


class TestMontrekModelChoiceFieldGetInitialLink(TestCase):
    def test_returns_matching_object(self):
        SatC1Factory(field_c1_str="match_me")
        queryset = HubCRepositoryOnlyStatic().receive()
        initial = {"field_c1_str": "match_me"}
        result = MontrekModelChoiceField.get_initial_link(
            initial, queryset, "field_c1_str", None, None
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.field_c1_str, "match_me")

    def test_returns_none_when_no_match(self):
        queryset = HubCRepositoryOnlyStatic().receive()
        initial = {"field_c1_str": "no_such_value"}
        result = MontrekModelChoiceField.get_initial_link(
            initial, queryset, "field_c1_str", None, None
        )
        self.assertIsNone(result)

    def test_uses_source_field_when_provided(self):
        SatC1Factory(field_c1_str="via_source")
        queryset = HubCRepositoryOnlyStatic().receive()
        initial = {"my_source_key": "via_source"}
        result = MontrekModelChoiceField.get_initial_link(
            initial, queryset, "field_c1_str", None, "my_source_key"
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.field_c1_str, "via_source")


# ---------------------------------------------------------------------------
# MontrekModelMultipleChoiceField
# ---------------------------------------------------------------------------


class TestMontrekModelMultipleChoiceField(TestCase):
    def test_get_widget_with_checkboxes_returns_checkbox_select_multiple(self):
        widget = MontrekModelMultipleChoiceField.get_widget("field_name", True)
        self.assertIsInstance(widget, forms.CheckboxSelectMultiple)

    def test_get_widget_without_checkboxes_returns_filtered_select(self):
        from django.contrib.admin.widgets import FilteredSelectMultiple

        widget = MontrekModelMultipleChoiceField.get_widget("field_name", False)
        self.assertIsInstance(widget, FilteredSelectMultiple)

    def test_get_initial_link_json_string_no_separator(self):
        SatC1Factory(field_c1_str="val1")
        SatC1Factory(field_c1_str="val2")
        queryset = HubCRepositoryOnlyStatic().receive()
        initial = {"field_c1_str": json.dumps(["val1", "val2"])}
        result = MontrekModelMultipleChoiceField.get_initial_link(
            initial, queryset, "field_c1_str", None, None
        )
        self.assertEqual(result.count(), 2)

    def test_get_initial_link_with_separator(self):
        SatC1Factory(field_c1_str="alpha")
        SatC1Factory(field_c1_str="beta")
        queryset = HubCRepositoryOnlyStatic().receive()
        initial = {"field_c1_str": "alpha,beta"}
        result = MontrekModelMultipleChoiceField.get_initial_link(
            initial, queryset, "field_c1_str", ",", None
        )
        self.assertEqual(result.count(), 2)

    def test_get_initial_link_non_string_returns_none(self):
        queryset = HubCRepositoryOnlyStatic().receive()
        initial = {"field_c1_str": ["val1", "val2"]}
        result = MontrekModelMultipleChoiceField.get_initial_link(
            initial, queryset, "field_c1_str", None, None
        )
        self.assertIsNone(result)

    def test_get_initial_link_missing_key_returns_none(self):
        queryset = HubCRepositoryOnlyStatic().receive()
        result = MontrekModelMultipleChoiceField.get_initial_link(
            {}, queryset, "field_c1_str", None, None
        )
        self.assertIsNone(result)

    def test_get_initial_link_invalid_json_returns_none(self):
        queryset = HubCRepositoryOnlyStatic().receive()
        initial = {"field_c1_str": "not valid json {["}
        result = MontrekModelMultipleChoiceField.get_initial_link(
            initial, queryset, "field_c1_str", None, None
        )
        self.assertIsNone(result)

    def test_get_initial_link_empty_string_json_returns_none(self):
        queryset = HubCRepositoryOnlyStatic().receive()
        initial = {"field_c1_str": ""}
        result = MontrekModelMultipleChoiceField.get_initial_link(
            initial, queryset, "field_c1_str", None, None
        )
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# MontrekModelCharChoiceField.clean
# ---------------------------------------------------------------------------


class TestMontrekModelCharChoiceFieldClean(TestCase):
    def _make_field(self, required=False):
        queryset = HubCRepositoryOnlyStatic().receive()
        return MontrekModelCharChoiceField(
            display_field="field_c1_str",
            queryset=queryset,
            required=required,
        )

    def test_clean_empty_not_required_returns_none(self):
        field = self._make_field(required=False)
        self.assertIsNone(field.clean(""))

    def test_clean_empty_required_raises_validation_error(self):
        field = self._make_field(required=True)
        with self.assertRaises(forms.ValidationError) as ctx:
            field.clean("")
        self.assertIn("No value given", str(ctx.exception))

    def test_clean_valid_value_returns_instance(self):
        SatC1Factory(field_c1_str="KNOWN")
        field = self._make_field()
        result = field.clean("KNOWN")
        self.assertEqual(result.field_c1_str, "KNOWN")

    def test_clean_no_match_raises_validation_error(self):
        field = self._make_field()
        with self.assertRaises(forms.ValidationError) as ctx:
            field.clean("NOTFOUND")
        self.assertIn("No matching object found!", str(ctx.exception))

    def test_clean_multiple_matches_raises_validation_error(self):
        SatC1Factory(field_c1_str="DUPLICATE")
        SatC1Factory(field_c1_str="DUPLICATE")
        field = self._make_field()
        with self.assertRaises(forms.ValidationError) as ctx:
            field.clean("DUPLICATE")
        self.assertIn("Multiple matching objects found!", str(ctx.exception))

    def test_get_initial_link_returns_value_from_initial(self):
        initial = {"my_key": "expected_value"}
        result = MontrekModelCharChoiceField.get_initial_link(
            initial, None, "display_field", source_field="my_key"
        )
        self.assertEqual(result, "expected_value")

    def test_get_initial_link_defaults_to_display_field(self):
        initial = {"display_field": "from_display"}
        result = MontrekModelCharChoiceField.get_initial_link(
            initial, None, "display_field"
        )
        self.assertEqual(result, "from_display")


# ---------------------------------------------------------------------------
# get_link_names — new behaviour: includes reverse M2M
# ---------------------------------------------------------------------------


class TestGetLinkNames(TestCase):
    def test_forward_m2m_included_for_hub_a(self):
        repo = HubARepository({})
        names = repo.get_link_names()
        self.assertIn("link_hub_a_hub_b", names)
        self.assertIn("link_hub_a_hub_c", names)

    def test_no_reverse_m2m_on_hub_a(self):
        repo = HubARepository({})
        names = repo.get_link_names()
        # HubA is always the source, never a M2M target
        self.assertNotIn("link_hub_b_hub_a", names)
        self.assertNotIn("link_hub_c_hub_a", names)

    def test_hub_d_includes_forward_and_reverse_m2m(self):
        repo = HubDRepository({})
        names = repo.get_link_names()
        # Forward: HubD → HubE
        self.assertIn("link_hub_d_hub_e", names)
        # Reverse: HubB → HubD (related_name="link_hub_d_hub_b")
        self.assertIn("link_hub_d_hub_b", names)
        # Reverse: HubC → HubD (related_name="link_hub_d_hub_c")
        self.assertIn("link_hub_d_hub_c", names)

    def test_hub_e_has_only_reverse_m2m(self):
        repo = HubERepository({})
        names = repo.get_link_names()
        # No forward M2M on HubE
        # Reverse: HubD → HubE (related_name="link_hub_e_hub_d")
        self.assertIn("link_hub_e_hub_d", names)

    def test_no_duplicates_in_link_names(self):
        for repo_class in (HubARepository, HubDRepository, HubERepository):
            names = repo_class({}).get_link_names()
            self.assertEqual(
                len(names), len(set(names)), msg=f"Duplicates in {repo_class.__name__}"
            )

    def test_skim_data_frame_keeps_reversed_link_column(self):
        sat_b = SatB1Factory(field_b1_str="skim_test")
        repo = HubDRepository(session_data={"user_id": 1})
        df = pd.DataFrame(
            {"field_d1_str": ["Test D"], "link_hub_d_hub_b": [sat_b.hub_entity]}
        )
        result = repo.skim_data_frame(df)
        self.assertIn("link_hub_d_hub_b", result.columns)

    def test_skim_data_frame_drops_unknown_columns(self):
        repo = HubDRepository(session_data={"user_id": 1})
        df = pd.DataFrame({"field_d1_str": ["Test"], "unknown_col": ["dropped"]})
        result = repo.skim_data_frame(df)
        self.assertNotIn("unknown_col", result.columns)
