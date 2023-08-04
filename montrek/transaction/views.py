from django.shortcuts import render
from django.shortcuts import redirect
from transaction.repositories.transaction_account_queries import (
    new_transaction_to_account,
)
from account.models import AccountStaticSatellite

# Create your views here.
#### Transaction Views ####


def transaction_add_form(request, account_id: int):
    account_statics = AccountStaticSatellite.objects.get(hub_entity=account_id)
    return render(
        request, "transaction_add_form.html", {"account_statics": account_statics}
    )


def transaction_add(request, account_id: int):
    new_transaction_to_account(
        account_id=account_id,
        transaction_date=request.POST["transaction_date"],
        transaction_amount=request.POST["transaction_amount"],
        transaction_price=request.POST["transaction_price"],
        transaction_description=request.POST["transaction_description"],
        transaction_type=None,
        transaction_category="",
    )
    return redirect(f"/account/{account_id}/view")

def transaction_view(request, transaction_id: int):
    return render(request, "transaction_view.html")
