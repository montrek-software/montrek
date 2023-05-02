
from django.shortcuts import render, redirect
from account.models import AccountHub, AccountStaticSatellite

# Create your views here.

def account_new(request):
    account_hub = AccountHub.objects.create()
    account_static_satellite = AccountStaticSatellite.objects.create(
        hub_entity=account_hub,
        account_name=request.POST['account_name'],
                                )
    return redirect('/account/list')

def account_new_form(request):
    return render(request, 'new_account_form.html')

def account_list(request):
    accounts_statics = AccountStaticSatellite.objects.all()
    return render(request, 
                  'account_list.html', 
                  {'items': accounts_statics})

def account_view(request, account_id: int):
    account_statics = AccountStaticSatellite.objects.get(hub_entity=account_id)
    return render(request,
                  'account_view.html',
                  {'account_statics': account_statics})
