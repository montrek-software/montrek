from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement, ActionElement
from baseclasses.pages import MontrekPage


class AccountOverviewPage(MontrekPage):
    page_title = "Accounts"

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
    def __init__(self, obj):
        super().__init__()
        self.obj = obj
        self.page_title = obj.account_name

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
                name="Overview",
                link=reverse(
                    "account_details", kwargs={"pk": account_id}
                ),
                html_id="tab_details",
                actions=(action_back, action_delete),
            ),
            TabElement(
                name="Transactions",
                link=reverse(
                    "bank_account_view_transactions", kwargs={"account_id": account_id}
                ),
                html_id="tab_transactions",
                actions=(action_back, action_new_transaction),
            ),
            TabElement(
                name="Graphs",
                link=reverse(
                    "bank_account_view_graphs", kwargs={"account_id": account_id}
                ),
                html_id="tab_graphs",
                actions=(action_back,),
            ),
            TabElement(
                name="Uploads",
                link=reverse(
                    "bank_account_view_uploads", kwargs={"account_id": account_id}
                ),
                html_id="tab_uploads",
                actions=(action_back, action_upload_csv),
            ),
            TabElement(
                name="Transaction Category Map",
                link=reverse(
                    "bank_account_view_transaction_category_map",
                    kwargs={"account_id": account_id},
                ),
                html_id="tab_transaction_category_map",
                actions=(action_back, action_add_transaction_category),
            ),
        ]
        return tabs
