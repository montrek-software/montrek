from django.shortcuts import render
from django.shortcuts import redirect
from django.views.generic import DetailView
from django.views.generic.edit import CreateView
from django.urls import reverse
from django.http import HttpResponseRedirect
from transaction.forms import TransactionSatelliteForm
from transaction.forms import TransactionCategoryMapSatelliteForm
from transaction.repositories.transaction_account_queries import (
    new_transaction_to_account,
)
from transaction.repositories.transaction_category_queries import (
    add_transaction_category_map_entry,
)
from transaction.models import TransactionSatellite
from transaction.models import TransactionCategoryMapSatellite
from account.models import AccountStaticSatellite
from account.models import AccountHub
from baseclasses.repositories import db_helper

class TransactionSatelliteDetailView(DetailView):
    model = TransactionSatellite
    template_name = 'transaction_view.html'  # The name of your HTML template
    context_object_name = 'transaction'  # This is what the object will be called in the template

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = TransactionSatelliteForm(instance=self.object)
        context['category'] = self.object.transaction_category
        return context

class TransactionCategoryMapTemplateView(CreateView):
    model = TransactionCategoryMapSatellite
    form_class = TransactionCategoryMapSatelliteForm
    template_name = 'transaction_category_map_form.html'  # The name of your HTML template
    context_object_name = 'transaction_category_map'

    def get_success_url(self):
        account_id = self.kwargs['account_id']
        return reverse('bank_account_view_transaction_category_map',
                       kwargs={'account_id': account_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['account_id'] = self.kwargs['account_id']
        return context

    def form_valid(self, form):
        account_id = self.kwargs['account_id']
        account_hub = db_helper.get_hub_by_id(account_id, AccountHub)
        add_transaction_category_map_entry(account_hub, form.cleaned_data)
        return HttpResponseRedirect(self.get_success_url())

class TransactionCategoryMapShowEntriesView(TransactionCategoryMapTemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pk'] = self.kwargs['pk']
        transaction_category_entry = TransactionCategoryMapSatellite.objects.get(
            pk=self.kwargs['pk']
        )
        context['form'] = TransactionCategoryMapSatelliteForm(
            instance=transaction_category_entry
        )
        return context

class TransactionCategoryMapCreateView(TransactionCategoryMapTemplateView):
    pass


class TransactionCategoryMapUpdateView(TransactionCategoryMapShowEntriesView):
    pass

class TransactionCategoryMapDeleteView(TransactionCategoryMapShowEntriesView):
    template_name = 'transaction_category_map_delete_form.html'  # The name of your HTML template

    def form_valid(self, form):
        transaction_category_entry = TransactionCategoryMapSatellite.objects.get(
            pk=self.kwargs['pk']
        )
        transaction_category_entry.hub_entity.is_deleted = True
        transaction_category_entry.hub_entity.save()
        return HttpResponseRedirect(self.get_success_url())


def _get_account_statics(account_id: int):
    account_hub = db_helper.get_hub_by_id(account_id, AccountHub)
    return db_helper.select_satellite(account_hub, AccountStaticSatellite )

def transaction_add_form(request, account_id: int):
    account_statics = _get_account_statics(account_id)
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
    account_statics = _get_account_statics(account_id)
    if account_statics.account_type == "BankAccount":
        return redirect(f"/account/{account_id}/bank_account_view/transactions")
    return redirect(f"/account/{account_id}/view")
