from django.shortcuts import render, redirect
from account.models import AccountHub, AccountStaticSatellite

# Create your views here.

def account_new(request):
    return redirect('/account/list')

def account_new_form(request):
    return render(request, 'new_account_form.html')

def account_list(request):
    return render(request, 'account_list.html')

