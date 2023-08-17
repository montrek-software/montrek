from django.shortcuts import render
from django.shortcuts import redirect
from django.views.generic import DetailView
from django.views.generic import ListView
from .forms import TransactionSatelliteForm
from transaction.repositories.transaction_account_queries import (
    new_transaction_to_account,
)
from transaction.repositories.transaction_account_queries import (
    get_transactions_by_account_id
)
from transaction.models import TransactionSatellite
from account.models import AccountStaticSatellite

class TransactionSatelliteDetailView(DetailView):
    model = TransactionSatellite
    template_name = 'transaction_view.html'  # The name of your HTML template
    context_object_name = 'transaction'  # This is what the object will be called in the template

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = TransactionSatelliteForm(instance=self.object)
        context['category'] = self.object.transaction_category
        return context

class AccountTransactionsListView(ListView):
    template_name = 'account_transactions_list.html'
    context_object_name = 'transactions'
    model = TransactionSatellite
    paginate_by = 10

    def get_queryset(self):
        account_id = self.kwargs['account_id']
        transactions = get_transactions_by_account_id(account_id)
        return transactions.order_by("-transaction_date").all()

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

