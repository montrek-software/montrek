from django.shortcuts import render
from django.shortcuts import redirect
from django.views.generic.edit import CreateView
from django.urls import reverse
from django.http import HttpResponseRedirect
from transaction.forms import TransactionCategoryMapSatelliteForm
from transaction.forms import TransactionCreateForm
from transaction.forms import TransactionCategoryMapCreateForm
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
from transaction.repositories.transaction_category_repository import (
    TransactionCategoryMapRepository,
)
from transaction.models import TransactionCategoryMapSatellite
from transaction.pages import TransactionPage
from transaction.pages import TransactionCategoryMapPage
from account.models import AccountHub
from account.pages import AccountPage
from account.repositories.account_repository import AccountRepository
from baseclasses.repositories import db_helper
from baseclasses.views import MontrekDetailView
from baseclasses.views import MontrekCreateView
from baseclasses.views import MontrekUpdateView
from baseclasses.dataclasses.table_elements import StringTableElement
from baseclasses.dataclasses.table_elements import DateTableElement
from baseclasses.dataclasses.table_elements import EuroTableElement
from baseclasses.dataclasses.table_elements import FloatTableElement
from baseclasses.dataclasses.table_elements import BooleanTableElement
from baseclasses.dataclasses.table_elements import LinkTextTableElement
from asset.models import AssetStaticSatellite
from asset.models import AssetHub


class TransactionDetailView(MontrekDetailView):
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
                url="account_view_transactions",
                kwargs={"pk": "account_id"},
                text="account_name",
                hover_text="View Account",
            ),
        ]


class FromAccountCreateViewMixin(MontrekCreateView):
    page_class = AccountPage
    account_link_name = ""

    def get_success_url(self):
        account_id = self.kwargs["account_id"]
        return reverse("account_view_transactions", kwargs={"pk": account_id})

    def get_form(self):
        form = super().get_form()
        account_hub = (
            AccountRepository({}).std_queryset().get(pk=self.kwargs["account_id"])
        )
        form[self.account_link_name].initial = account_hub
        return form

    def get_context_data(self, **kwargs):
        # Set pk to make account form work
        self.kwargs["pk"] = self.kwargs["account_id"]
        context = super().get_context_data(**kwargs)
        return context


class TransactionCreateFromAccountView(FromAccountCreateViewMixin):
    repository = TransactionRepository
    form_class = TransactionCreateForm
    account_link_name = "link_transaction_account"


class TransactionUpdateView(MontrekUpdateView):
    repository = TransactionRepository
    page_class = TransactionPage
    form_class = TransactionCreateForm

    def get_success_url(self):
        transaction_pk = self.kwargs["pk"]
        return reverse("transaction_details", kwargs={"pk": transaction_pk})

    def get_form(self):
        edit_object = (
            self.repository({}).get_queryset_with_account().get(pk=self.kwargs["pk"])
        )
        initial = self.repository_object.object_to_dict(edit_object)
        initial["link_transaction_account"] = edit_object.link_transaction_account.get()
        return self.form_class(repository=self.repository_object, initial=initial)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["account_id"] = context["form"].initial["link_transaction_account"].id
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





class TransactionCategoryMapDetailView(MontrekDetailView):
    repository = TransactionCategoryMapRepository
    page_class = TransactionCategoryMapPage
    title = "Transaction Category Map Details"

    @property
    def elements(self) -> list:
        return [
            StringTableElement(
                attr="value",
                name="Value",
            ),
            StringTableElement(
                attr="field",
                name="Field",
            ),
            StringTableElement(
                attr="category",
                name="Category",
            ),
            BooleanTableElement(
                attr="is_regex",
                name="Is Regex",
            ),
            LinkTextTableElement(
                name="Account",
                url="account_view_transaction_category_map",
                kwargs={"pk": "account_id"},
                text="account_name",
                hover_text="View Account",
            ),
        ]


class TransactionCategoryMapCreateView(FromAccountCreateViewMixin):
    repository = TransactionCategoryMapRepository
    account_link_name = "link_transaction_category_map_account"
    form_class = TransactionCategoryMapCreateForm

    def get_form(self):
        form = super().get_form()
        initial = {}
        counterparty = self.kwargs.get("counterparty", None)
        if counterparty:
            initial["value"] = counterparty
            initial["field"] = "Transaction Party"

        iban = self.kwargs.get("iban", None)
        if iban:
            initial["value"] = iban
            initial["field"] = TransactionCategoryMapSatellite.TRANSACTION_PARTY_IBAN
        for key, value in initial.items():
            form[key].initial = value
        return form

    def form_valid(self, form):
        return_url = super().form_valid(form)
        return return_url




class TransactionCategoryMapUpdateView(
):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag"] = "Edit"
        return context


class TransactionCategoryMapDeleteView(
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
