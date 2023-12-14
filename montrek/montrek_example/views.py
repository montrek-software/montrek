from django.shortcuts import render
from baseclasses.views import MontrekCreateView
from montrek_example.repositories.hub_a_repository import HubARepository
from montrek_example.forms import HubACreateForm

# Create your views here.

class MontrekExampleACreate(MontrekCreateView):
    repository=HubARepository
    form_class=HubACreateForm

