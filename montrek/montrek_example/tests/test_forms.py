from django.forms import PasswordInput
from django.test import TestCase
from montrek_example.forms import ExampleABaseForm, ExampleACreateForm
from montrek_example.repositories.hub_a_repository import (
    HubARepository,
    HubARepository5,
)
from montrek_example.tests.factories.montrek_example_factories import SatC1Factory


class TestMontrekCreateForm(TestCase):
    def test_link_choice_char_field__expect_no_link_id(self):
        repository = HubARepository({})
        test_data = {
            "field_a1_str": "test",
            "field_a1_int": 1,
            "field_a2_str": "test2",
            "field_a2_float": 2.0,
        }
        test_form = ExampleACreateForm(data=test_data, repository=repository)
        self.assertTrue(test_form.is_valid())
        self.assertEqual(test_form.fields["field_a2_float"].label, "Renamed Label")

    def test_link_choice_char_field__no_object(self):
        repository = HubARepository({})
        test_data = {
            "field_a1_str": "test",
            "field_a1_int": 1,
            "field_a2_str": "test2",
            "field_a2_float": 2.0,
            "link_hub_a_hub_c": "TESTID123",
        }
        test_form = ExampleACreateForm(data=test_data, repository=repository)
        self.assertFalse(test_form.is_valid())
        self.assertEqual(
            test_form.errors, {"link_hub_a_hub_c": ["No matching object found!"]}
        )

    def test_link_choice_char_field__ok(self):
        test_sat = SatC1Factory.create(field_c1_str="TESTID123")
        repository = HubARepository({})
        test_data = {
            "field_a1_str": "test",
            "field_a1_int": 1,
            "field_a2_str": "test2",
            "field_a2_float": 2.0,
            "link_hub_a_hub_c": "TESTID123",
        }
        test_form = ExampleACreateForm(data=test_data, repository=repository)
        self.assertTrue(test_form.is_valid())
        test_instance = test_form.cleaned_data["link_hub_a_hub_c"]
        self.assertEqual(test_instance.hub, test_sat.hub_entity)

    def test_link_choice_char_field__multiple_instances(self):
        SatC1Factory.create(field_c1_str="TESTID123")
        SatC1Factory.create(field_c1_str="TESTID123")
        repository = HubARepository({})
        test_data = {
            "field_a1_str": "test",
            "field_a1_int": 1,
            "field_a2_str": "test2",
            "field_a2_float": 2.0,
            "link_hub_a_hub_c": "TESTID123",
        }
        test_form = ExampleACreateForm(data=test_data, repository=repository)
        self.assertFalse(test_form.is_valid())
        self.assertEqual(
            test_form.errors, {"link_hub_a_hub_c": ["Multiple matching objects found!"]}
        )

    def test_link_choice_char_field__init(self):
        test_sat = SatC1Factory.create(field_c1_str="TESTID123")
        repository = HubARepository({})
        initial_data = {"link_hub_a_hub_c": test_sat.hub_entity}
        test_data = {
            "field_a1_str": "test",
            "field_a1_int": 1,
            "field_a2_str": "test2",
            "field_a2_float": 2.0,
        }
        test_form = ExampleACreateForm(
            initial=initial_data, data=test_data, repository=repository
        )
        self.assertTrue(test_form.is_valid())

    def test_link_choice_field__readonly(self):
        repository = HubARepository({})
        test_form = ExampleACreateForm(repository=repository)
        self.assertEqual(
            test_form.fields["link_hub_a_hub_b"].widget.attrs["readonly"], "readonly"
        )

    def test_encrypted_value_in_form(self):
        repository = HubARepository5({})
        test_form = ExampleABaseForm(repository=repository)
        self.assertIsInstance(test_form.fields["secret_field"].widget, PasswordInput)
