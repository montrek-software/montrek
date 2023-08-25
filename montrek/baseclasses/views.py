from django.shortcuts import render

# Create your views here.

def home(request):
    return render(request, "home.html")

def under_construction(request):
    return render(request, "under_construction.html")

