from django.test import TestCase
from montrek_example.tests.factories.montrek_example_factories import SatC1Factory

from montrek_example.forms import ExampleACreateForm
from montrek_example.repositories.hub_a_repository import HubARepository


class TestMontrekCreateForm(TestCase):
    def test_link_choice_char_field__expect_link_id(self):
        repository = HubARepository({})
        test_data = {
            "field_a1_str": "test",
            "field_a1_int": 1,
            "field_a2_str": "test2",
            "field_a2_float": 2.0,
        }
        test_form = ExampleACreateForm(data=test_data, repository=repository)
        self.assertFalse(test_form.is_valid())

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
        self.assertTrue(test_form.is_valid())
