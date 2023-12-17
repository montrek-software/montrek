from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement, ActionElement
from baseclasses.pages import MontrekPage
from account.repositories.account_repository import AccountRepository


class AccountOverviewPage(MontrekPage):
    page_title = "Accounts"
    show_date_range_selector = True

    def get_tabs(self):
        action_new_account = ActionElement(
            icon="plus",
            link=reverse("account_new_form"),
            action_id="id_new_account",
            hover_text="Add new Account",
        )
        overview_tab = TabElement(
            name="Account List",
            link=reverse("account"),
            html_id="tab_account_list",
            active="active",
            actions=(action_new_account,),
        )
        return (overview_tab,)


class AccountPage(MontrekPage):
    show_date_range_selector = True

    def __init__(self, repository, **kwargs):
        super().__init__(repository, **kwargs)
        if 'pk' not in kwargs:
            raise ValueError("AccountPage needs pk specified in url!")
        self.obj = self.repository.std_queryset().get(pk=kwargs['pk'])
        self.page_title = self.obj.account_name

    def get_tabs(self):
        account_id = self.obj.pk
        action_back = ActionElement(
            icon="chevron-left",
            link=reverse("account"),
            action_id="list_back",
            hover_text="Back to account list",
        )
        action_delete = ActionElement(
            icon="trash",
            link=reverse("account_delete_form", kwargs={"account_id": account_id}),
            action_id="delete_account",
            hover_text="Delete account",
        )
        action_new_transaction = ActionElement(
            icon="plus",
            link=reverse("transaction_add_form", kwargs={"account_id": account_id}),
            action_id="add_transaction",
            hover_text="Add transaction",
        )
        action_upload_csv = ActionElement(
            icon="upload",
            link=reverse(
                "upload_transaction_to_account_file", kwargs={"account_id": account_id}
            ),
            action_id="id_transactions_upload",
            hover_text="Upload transactions from csv file",
        )
        action_add_transaction_category = ActionElement(
            icon="plus",
            link=reverse(
                "transaction_category_add_form", kwargs={"account_id": account_id}
            ),
            action_id="id_add_transaction_category",
            hover_text="Add transaction category",
        )
        action_update_asset_prices = ActionElement(
            icon="refresh",
            link=reverse("update_asset_prices", kwargs={"account_id": account_id}),
            action_id="id_update_asset_prices",
            hover_text="Update asset prices",
        )

        tabs = [
            TabElement(
                name="Details",
                link=reverse(
                    "account_details", kwargs={"pk": account_id}
                ),
                html_id="tab_details",
                actions=(action_back, action_delete),
            ),
            TabElement(
                name="Transactions",
                link=reverse(
                    "bank_account_view_transactions", kwargs={"pk": account_id}
                ),
                html_id="tab_transactions",
                actions=(action_back, action_new_transaction),
            ),
            TabElement(
                name="Graphs",
                link=reverse(
                    "account_view_graphs", kwargs={"pk": account_id}
                ),
                html_id="tab_graphs",
                actions=(action_back,),
            ),
            TabElement(
                name="Uploads",
                link=reverse(
                    "account_view_uploads", kwargs={"pk": account_id}
                ),
                html_id="tab_uploads",
                actions=(action_back, action_upload_csv),
            ),
            TabElement(
                name="Transaction Category Map",
                link=reverse(
                    "account_view_transaction_category_map",
                    kwargs={"pk": account_id},
                ),
                html_id="tab_transaction_category_map",
                actions=(action_back, action_add_transaction_category),
            ),
        ]
        if self.obj.account_type in ["Depot"]:
            tabs.insert(1,
                TabElement(
                    name="Depot",
                    link=reverse('account_view_depot', kwargs={'pk': account_id}),
                    html_id="tab_depot",
                    actions = (action_back, action_update_asset_prices)
                )
            )
        return tabs
