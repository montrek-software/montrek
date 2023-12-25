from django.shortcuts import render
from django.shortcuts import redirect
from django.views.generic import DetailView
from django.views.generic.edit import CreateView
from django.urls import reverse
from django.http import HttpResponseRedirect
from transaction.forms import TransactionCategoryMapSatelliteForm
from transaction.forms import TransactionCreateForm
from transaction.repositories.transaction_account_queries import (
    new_transaction_to_account,
)
from transaction.repositories.transaction_category_queries import (
    add_transaction_category_map_entry,
)
from transaction.repositories.transaction_category_queries import (
    set_transaction_category_by_map_entry,
)
from transaction.repositories.transaction_repository import TransactionRepository
from transaction.models import TransactionCategoryMapSatellite
from transaction.pages import TransactionPage
from account.models import AccountStaticSatellite
from account.models import AccountHub
from account.pages import AccountPage
from baseclasses.repositories import db_helper
from baseclasses.views import MontrekDetailView
from baseclasses.views import MontrekCreateView
from baseclasses.dataclasses.table_elements import StringTableElement
from baseclasses.dataclasses.table_elements import DateTableElement
from baseclasses.dataclasses.table_elements import EuroTableElement
from baseclasses.dataclasses.table_elements import FloatTableElement
from baseclasses.dataclasses.table_elements import LinkTextTableElement
from asset.models import AssetStaticSatellite
from asset.models import AssetHub
from account.repositories.account_repository import AccountRepository


class TransactionSatelliteDetailView(MontrekDetailView):
    repository = TransactionRepository
    page_class = TransactionPage
    tab = "tab_details"
    title = "Transaction Details"

    def get_queryset(self):
        return self.repository(self.request).get_queryset_with_account()

    @property
    def elements(self) -> list:
        return [
            DateTableElement(
                attr="transaction_date",
                name="Date",
            ),
            FloatTableElement(
                attr="transaction_amount",
                name="Amount",
            ),
            EuroTableElement(
                attr="transaction_price",
                name="Price",
            ),
            EuroTableElement(
                attr="transaction_value",
                name="Value",
            ),
            StringTableElement(
                attr="transaction_description",
                name="Description",
            ),
            StringTableElement(
                attr="transaction_party",
                name="Party",
            ),
            StringTableElement(
                attr="transaction_category",
                name="Category",
            ),
            LinkTextTableElement(
                name="Account",
                url="account_details",
                kwargs={"pk": "account_id"},
                text="account_name",
                hover_text="View Account",
            ),
        ]


class TransactionCreateFromAccountView(MontrekCreateView):
    repository = TransactionRepository
    page_class = AccountPage
    form_class = TransactionCreateForm

    def get_success_url(self):
        account_id = self.kwargs["account_id"]
        return reverse(
            "account_details", kwargs={"pk": account_id}
        )

    def get_form(self):
        form = super().get_form()
        account_hub = (
            AccountRepository({}).std_queryset().get(pk=self.kwargs["account_id"])
        )
        form['link_transaction_account'].initial = account_hub
        return form

    def get_context_data(self, **kwargs):
        # Set pk to make account form work
        self.kwargs["pk"] = self.kwargs["account_id"]
        context = super().get_context_data(**kwargs)
        return context


class SuccessURLTransactionCategoryMapMixin(
    CreateView
):  # pylint: disable=too-few-public-methods
    def get_success_url(self):
        account_id = self.kwargs["account_id"]
        return reverse(
            "account_view_transaction_category_map", kwargs={"pk": account_id}
        )


class SuccessURLTransactionTableMixin(
    CreateView
):  # pylint: disable=too-few-public-methods
    def get_success_url(self):
        account_id = self.kwargs["account_id"]
        return reverse(
            "bank_account_view_transactions", kwargs={"account_id": account_id}
        )


class TransactionCategoryMapTemplateView(CreateView):
    model = TransactionCategoryMapSatellite
    form_class = TransactionCategoryMapSatelliteForm
    template_name = (
        "transaction_category_map_form.html"  # The name of your HTML template
    )
    context_object_name = "transaction_category_map"

    def get_initial(self):
        initial = super().get_initial()

        counterparty = self.kwargs.get("counterparty", None)
        if counterparty:
            initial["value"] = counterparty
            initial["field"] = "Transaction Party"

        iban = self.kwargs.get("iban", None)
        if iban:
            initial["value"] = iban
            initial["field"] = TransactionCategoryMapSatellite.TRANSACTION_PARTY_IBAN
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["account_id"] = self.kwargs["account_id"]
        context["iban"] = self.kwargs.get("iban", None)
        context["counterparty"] = self.kwargs.get("counterparty", None)
        return context

    def form_valid(self, form):
        account_id = self.kwargs["account_id"]
        account_hub = db_helper.get_hub_by_id(account_id, AccountHub)
        transaction_category_map_entry = add_transaction_category_map_entry(
            account_hub, form.cleaned_data
        )
        set_transaction_category_by_map_entry(
            transaction_category_map_entry,
        )
        return HttpResponseRedirect(self.get_success_url())


class TransactionCategoryMapShowEntriesView(
    TransactionCategoryMapTemplateView, SuccessURLTransactionCategoryMapMixin
):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pk"] = self.kwargs["pk"]
        transaction_category_entry = TransactionCategoryMapSatellite.objects.get(
            pk=self.kwargs["pk"]
        )
        context["form"] = TransactionCategoryMapSatelliteForm(
            instance=transaction_category_entry
        )
        return context


class TransactionCategoryMapCreateView(
    TransactionCategoryMapTemplateView, SuccessURLTransactionCategoryMapMixin
):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag"] = "Add"
        return context


class TransactionCategoryMapCreateFromTransactionView(
    TransactionCategoryMapCreateView,
    SuccessURLTransactionTableMixin,
):
    pass


class TransactionCategoryMapUpdateView(
    TransactionCategoryMapShowEntriesView, SuccessURLTransactionCategoryMapMixin
):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag"] = "Edit"
        return context


class TransactionCategoryMapDeleteView(
    TransactionCategoryMapShowEntriesView, SuccessURLTransactionCategoryMapMixin
):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag"] = "Delete"
        return context

    def form_valid(self, form):
        transaction_category_entry = TransactionCategoryMapSatellite.objects.get(
            pk=self.kwargs["pk"]
        )
        transaction_category_entry.hub_entity.is_deleted = True
        transaction_category_entry.hub_entity.save()
        return HttpResponseRedirect(self.get_success_url())


def _get_account_statics(account_id: int):
    account_hub = db_helper.get_hub_by_id(account_id, AccountHub)
    return db_helper.select_satellite(account_hub, AccountStaticSatellite)


def transaction_add_form(request, account_id: int):
    account_statics = _get_account_statics(account_id)
    return render(
        request,
        "transaction_add_form.html",
        {
            "account_statics": account_statics,
            "assets": AssetStaticSatellite.objects.all(),
        },
    )


def transaction_add(request, account_id: int):
    asset_name = request.POST["asset"]
    if asset_name != "None":
        asset_hub_id = int(asset_name[asset_name.find("<") + 1 : asset_name.find(">")])
        asset_hub = db_helper.get_hub_by_id(asset_hub_id, AssetHub)
        transaction_party = asset_hub.asset_static_satellite.last().asset_name
    else:
        transaction_party = "UNKNOWN"
    transaction_hub = new_transaction_to_account(
        account_id=account_id,
        transaction_date=request.POST["transaction_date"],
        transaction_amount=request.POST["transaction_amount"],
        transaction_price=request.POST["transaction_price"],
        transaction_description=request.POST["transaction_description"],
        transaction_party=transaction_party,
        transaction_type=None,
        transaction_category="",
    )
    account_statics = _get_account_statics(account_id)
    if asset_name != "None":
        transaction_hub.link_transaction_asset.add(asset_hub)
    if account_statics.account_type in ["BankAccount", "Depot"]:
        return redirect(f"/account/{account_id}/account_view/transactions")
    return redirect(f"/account/{account_id}/view")
