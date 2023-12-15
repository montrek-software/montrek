from django.shortcuts import render
from baseclasses.views import MontrekCreateView
from montrek_example.repositories.hub_a_repository import HubARepository
from montrek_example.forms import HubACreateForm
from montrek_example.models import SatA1

# Create your views here.

class MontrekExampleACreate(MontrekCreateView):
    repository=HubARepository
    form_class=HubACreateForm

