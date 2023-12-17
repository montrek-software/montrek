from django.shortcuts import render
from django.urls import reverse
from baseclasses.views import MontrekCreateView
from baseclasses.views import MontrekListView
from montrek_example.repositories.hub_a_repository import HubARepository
from montrek_example.forms import SatelliteA1CreateForm
from montrek_example.forms import SatelliteA2CreateForm
from montrek_example.models import SatA1
from montrek_example.pages import MontrekExampleAAppPage

from baseclasses.dataclasses.table_elements import StringTableElement
from baseclasses.dataclasses.table_elements import FloatTableElement
from baseclasses.dataclasses.table_elements import IntTableElement

# Create your views here.


class MontrekExampleACreate(MontrekCreateView):
    repository = HubARepository
    page_class = MontrekExampleAAppPage
    form_classes = [SatelliteA1CreateForm, SatelliteA2CreateForm]
    success_url = "montrek_example_a_list"


class MontrekExampleAList(MontrekListView):
    repository = HubARepository
    page_class = MontrekExampleAAppPage
    tab = "tab_example_a_list"

    @property
    def elements(self) -> list:
        return (
            StringTableElement(name="A1 String", attr="field_a1_str"),
            IntTableElement(name="A1 Int", attr="field_a1_int"),
            StringTableElement(name="A2 String", attr="field_a2_str"),
            FloatTableElement(name="A2 Float", attr="field_a2_float"),
        )
