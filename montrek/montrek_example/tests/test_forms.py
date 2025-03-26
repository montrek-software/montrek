from django.test import TestCase

from montrek_example.forms import ExampleACreateForm
from montrek_example.repositories.hub_a_repository import HubARepository


class TestMontrekCreateForm(TestCase):
    def test_link_choice_char_field(self):
        repository = HubARepository({})
        test_form = ExampleACreateForm(repository=repository)
