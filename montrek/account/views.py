
from django.shortcuts import render, redirect
from django.db import models
from account.models import AccountHub 
from account.models import AccountStaticSatellite
from account.models import BankAccountPropertySatellite
from account.models import BankAccountStaticSatellite
from transaction.model_utils import get_transactions_by_account_id
from account.model_utils import new_account
from credit_institution.model_utils import get_credit_institution_by_account_id
from credit_institution.model_utils import new_credit_institution_to_account
from credit_institution.models import CreditInstitutionStaticSatellite
from credit_institution.models import CreditInstitutionHub
from baseclasses.model_utils import new_link_entry
from baseclasses.model_utils import new_satellite_entry

# Create your views here.

#### Account Views ####
def account_new(request):
    account_type = request.POST.get('account_type', 'Other')
    account_name = request.POST['account_name']
    if account_type == 'Other':
        new_account(request.POST['account_name'])
        return redirect('/account/list')
    elif account_type == 'Bank Account':
        return redirect(f'/account/bank_account/new_form/{account_name}')
    else:
        return render(request,
                      'under_construction.html')


def account_new_form(request):
    account_types = AccountStaticSatellite.AccountType.choices
    return render(request, 
                  'new_account_form.html',
                 {'account_types': account_types})

def account_list(request):
    accounts_statics = AccountHub.objects.all().prefetch_related(
        'accountstaticsatellite_set',
        'bankaccountpropertysatellite_set')
    return render(request, 
                  'account_list.html', 
                  {'items': accounts_statics})

def account_view_data(account_id: int):
    account_statics = AccountStaticSatellite.objects.get(hub_entity=account_id)
    account_transactions = get_transactions_by_account_id(account_id).all()
    return {'account_statics': account_statics,
            'account_transactions': account_transactions,
           }

def account_view(request, account_id: int):
    account_data = account_view_data(account_id)
    return render(request,
                  'account_view.html',
                  account_data
                 )
def account_delete(request, account_id: int):
    account_statics = AccountStaticSatellite.objects.get(hub_entity=account_id)
    account_statics.delete()
    account = AccountHub.objects.get(id=account_id)
    account.delete()
    return redirect('/account/list')

def account_delete_form(request, account_id: int):
    account_statics = AccountStaticSatellite.objects.get(hub_entity=account_id)
    return render(request,
                  'account_delete_form.html',
                  {'account_statics': account_statics})


#### Bank Account Views ####

def bank_account_new_form(request, account_name: str):
    return render(request,
                  'bank_account_new_form.html',
                  {'credit_institutions':
                   CreditInstitutionStaticSatellite.objects.all(),
                  'account_name': account_name,
                  })

def bank_account_new(request, account_name: str):
    account_hub = new_account(account_name,
                              'BankAccount')
    BankAccountPropertySatellite.objects.create(
        hub_entity=account_hub,
    )
    new_satellite_entry(
        hub_entity=account_hub,
        satellite_class=BankAccountStaticSatellite,
        bank_account_iban=request.POST['bank_account_iban'],
    )
    credit_institution_name = request.POST['credit_institution_name']
    new_credit_institution_to_account(credit_institution_name, account_hub )
    return redirect('/account/list')

def bank_account_view_data(account_id: int):
    account_data = account_view_data(account_id)
    bank_account_static_satellite = BankAccountStaticSatellite.objects.get(
        hub_entity=account_id)
    account_data['bank_account_statics'] = bank_account_static_satellite
    account_data['credit_institution'] = get_credit_institution_by_account_id(account_id)
    return account_data

def bank_account_view(request, account_id: int):
    account_data = bank_account_view_data(account_id)
    return render(request,
                  'bank_account_view.html',
                  account_data
                 )
