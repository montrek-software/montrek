
from django.shortcuts import render, redirect
from django.db import models
from account.models import AccountHub 
from account.models import AccountStaticSatellite
from account.models import BankAccountPropertySatellite
from account.model_utils import new_transaction_to_account
from account.model_utils import get_transactions_by_account_id
from account.model_utils import get_credit_institution_by_account_id
from account.model_utils import new_account
from credit_institution.model_utils import new_credit_institution
from credit_institution.models import CreditInstitutionStaticSatellite
from credit_institution.models import CreditInstitutionHub
from link_tables.model_utils import new_account_credit_instition_link

# Create your views here.

#### Account Views ####
def account_new(request):
    account_type = request.POST['account_type']
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

#### Transaction Views ####

def transaction_add_form(request, account_id: int):
    account_statics = AccountStaticSatellite.objects.get(hub_entity=account_id)
    return render(request,
                  'transaction_add_form.html',
                  {'account_statics': account_statics})

def transaction_add(request, account_id: int):
    new_transaction_to_account(
        account_id=account_id, 
        transaction_date=request.POST['transaction_date'],
        transaction_amount= request.POST['transaction_amount'],
        transaction_price= request.POST['transaction_price'],
        transaction_description=request.POST['transaction_description'],
        transaction_type="",
        transaction_category="",
    )
    return redirect(f'/account/{account_id}/view')

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
    credit_institution_name = request.POST['credit_institution_name']
    credit_institution_hub = CreditInstitutionHub.objects.prefetch_related('creditinstitutionstaticsatellite_set').filter(
        creditinstitutionstaticsatellite__credit_institution_name=credit_institution_name)
    if len(credit_institution_hub) == 0:
        credit_institution_hub = new_credit_institution(credit_institution_name)
    new_account_credit_instition_link(account_hub, credit_institution_hub[0])
    return redirect('/account/list')

def bank_account_view_data(account_id: int):
    account_data = account_view_data(account_id)
    account_data['credit_institution'] = get_credit_institution_by_account_id(account_id).last()
    return account_data

def bank_account_view(request, account_id: int):
    account_data = bank_account_view_data(account_id)
    return render(request,
                  'bank_account_view.html',
                  account_data
                 )
