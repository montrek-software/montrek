from django.shortcuts import render
from baseclasses.dataclasses.nav_bar_model import NavBarModel

# Create your views here.

def home(request):
    return render(request, "home.html")

def under_construction(request):
    return render(request, "under_construction.html")

def navbar(request):
    nav_apps = [NavBarModel('account'), NavBarModel('credit_institution')]
    return render(request, "navbar.html", {"nav_apps": nav_apps})
