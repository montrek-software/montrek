import os
import time
from typing import List
from unittest.mock import patch
import pandas as pd
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import tag
from django.utils import timezone
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

from account.models import AccountStaticSatellite
from account.tests.factories.account_factories import AccountHubFactory
from account.tests.factories.account_factories import AccountStaticSatelliteFactory
from account.tests.factories.account_factories import (
    BankAccountPropertySatelliteFactory,
)
from account.tests.factories.account_factories import BankAccountStaticSatelliteFactory
from asset.models import AssetStaticSatellite
from transaction.tests.factories.transaction_factories import TransactionHubFactory
from transaction.tests.factories.transaction_factories import (
    TransactionSatelliteFactory,
)
from transaction.tests.factories.transaction_factories import (
    TransactionTypeSatelliteFactory,
)
from credit_institution.tests.factories.credit_institution_factories import (
    CreditInstitutionStaticSatelliteFactory,
)
from baseclasses.repositories.db_helper import get_hub_ids_by_satellite_attribute
from baseclasses.models import MontrekSatelliteABC

MAX_WAIT = 10


def wait_for_browser_action(browser_action):
    def inner_function(*args, **kwargs):
        start_time = time.time()
        while True:
            try:
                browser_action(*args, **kwargs)
                return
            except (AssertionError, WebDriverException) as exep:
                if time.time() - start_time > MAX_WAIT:
                    raise exep
                time.sleep(0.5)

    return inner_function


class MontrekFunctionalTest(StaticLiveServerTestCase):
    def setUp(self):
        try:
            self.browser = webdriver.Chrome()
        except WebDriverException:
            self.browser = webdriver.Chrome("/usr/bin/chromedriver")

    def tearDown(self):
        self.browser.quit()

    @wait_for_browser_action
    def check_for_row_in_table(self, row_content: List[str], table_id: str):
        table = self.browser.find_element(By.ID, table_id)
        rows = table.find_elements(By.TAG_NAME, "td")
        for row_text in row_content:
            self.assertIn(row_text, [row.text for row in rows])

    def find_object_hub_id(
        self, satellite_model: MontrekSatelliteABC, object_name: str, object_field: str
    ):
        # Since the table ids depend on what has been in the DB before the test
        # ran, we need to find the id of the object we are looking for
        hub_entity_id = get_hub_ids_by_satellite_attribute(
            satellite_model, object_field, object_name
        )[0]
        return hub_entity_id


class AccountFunctionalTests(MontrekFunctionalTest):
    @tag("functional")
    def test_add_new_account(self):
        # The user visits the new account form
        self.browser.get(self.live_server_url + "/account/list")
        self.browser.find_element(By.ID, "id_new_account").click()
        # The page title is 'Montrek'
        self.assertIn("Montrek", self.browser.title)
        # The header line says 'Add new Account'
        header_text = self.browser.find_element(By.TAG_NAME, "h1").text
        self.assertIn("Add new Account", header_text)
        # He enters 'Billy's account' into the Account Name Box
        new_account_name_box = self.browser.find_element(By.ID, "id_account_new__name")
        new_account_name_box.send_keys("Billy's account")
        # When he hits the submit button, he is directed to the accounts-list,
        # where he finds his new account listed
        self.browser.find_element(By.ID, "id_account_new__submit").click()
        header_text = self.browser.find_element(By.ID, "id_tab_account_list").text
        self.assertIn("Account List", header_text)
        self.check_for_row_in_table(["Billy's account"], "id_montrek_table_list")

    @tag("functional")
    def test_access_account_in_list(self):
        # The user sets up two new accounts
        self.browser.get(self.live_server_url + "/account/new_form")
        new_account_name_box = self.browser.find_element(By.ID, "id_account_new__name")
        new_account_name_box.send_keys("Billy's account")
        self.browser.find_element(By.ID, "id_account_new__submit").click()
        time.sleep(0.1)
        self.browser.get(self.live_server_url + "/account/new_form")
        new_account_name_box = self.browser.find_element(By.ID, "id_account_new__name")
        new_account_name_box.send_keys("Billy's second account")
        self.browser.find_element(By.ID, "id_account_new__submit").click()
        # He clicks on the first account link in the list
        first_id = self.find_object_hub_id(
            AccountStaticSatellite, "Billy's account", "account_name"
        )
        self.browser.find_element(By.ID, f"id__account_{first_id}_view").click()
        # The name of the Account is shown in the header
        header_text = self.browser.find_element(By.ID, "page_title").text
        self.assertIn("Billy's account", header_text)
        # After clicking on the back button he is back at the list
        self.browser.find_element(By.ID, "list_back").click()
        header_text = self.browser.find_element(By.ID, "id_tab_account_list").text
        self.assertIn("Account List", header_text)
        # He clicks on the second link and finds the account's name
        second_id = self.find_object_hub_id(
            AccountStaticSatellite, "Billy's second account", "account_name"
        )
        self.browser.find_element(By.ID, f"id__account_{second_id}_view").click()
        # The name of the Account is shown in the header
        header_text = self.browser.find_element(By.TAG_NAME, "h1").text
        self.assertIn("Billy's second account", header_text)
        # After clicking on the back button he is back at the list
        self.browser.find_element(By.ID, "list_back").click()
        header_text = self.browser.find_element(By.ID, "id_tab_account_list").text
        self.assertIn("Account List", header_text)
        # He now wants to delete the first account
        self.browser.find_element(By.ID, f"id__account_{first_id}_view").click()
        # He clicks on the delete button
        self.browser.find_element(By.ID, "delete_account").click()
        # He is asked to confirm the deletion
        header_text = self.browser.find_element(By.TAG_NAME, "h1").text
        self.assertIn("Delete Account", header_text)
        # He clicks on the delete button
        self.browser.find_element(By.ID, "delete_account").click()
        # He is back at the list and the first account is gone
        header_text = self.browser.find_element(By.ID, "id_tab_account_list").text
        self.assertIn("Account List", header_text)
        self.check_for_row_in_table(["Billy's second account"], "id_montrek_table_list")
        self.assertNotIn("Billy's account", self.browser.page_source)


class TransactionFunctionalTest(MontrekFunctionalTest):
    def setUp(self):
        super().setUp()
        self.test_account = AccountStaticSatelliteFactory()
        TransactionTypeSatelliteFactory.create(typename="INCOME")
        TransactionTypeSatelliteFactory.create(typename="EXPANSE")

    @tag("functional")
    def test_add_transaction_to_account(self):
        last_account_name = self.test_account.account_name
        account_id = self.test_account.hub_entity.id
        # The user visists the account page
        self.browser.get(self.live_server_url + f"/account/{account_id}/view")
        # He clicks on the add transaction button
        self.browser.find_element(By.ID, "add_transaction").click()
        # He is directed to the transaction form
        header_text = self.browser.find_element(By.TAG_NAME, "h1").text
        self.assertIn(f"Add transaction to {last_account_name}", header_text)
        # He enters the transaction data
        new_transaction_name_box = self.browser.find_element(
            By.ID, "id_transaction_new__name"
        )
        new_transaction_name_box.send_keys("Billy's transaction")
        new_transaction_amount_box = self.browser.find_element(
            By.ID, "id_transaction_new__amount"
        )
        new_transaction_amount_box.send_keys("3")
        new_transaction_price_box = self.browser.find_element(
            By.ID, "id_transaction_new__price"
        )
        new_transaction_price_box.send_keys("100.00")
        new_transaction_date_box = self.browser.find_element(
            By.ID, "id_transaction_new__date"
        )
        new_transaction_date_box.send_keys("01/01/2022")
        # He hits the submit button
        self.browser.find_element(By.ID, "id_transaction_new__submit").click()
        # He is directed back to the account page
        header_text = self.browser.find_element(By.TAG_NAME, "h1").text
        self.assertIn(last_account_name, header_text)
        # He sees the new transaction in the list
        transaction_list_title = self.browser.find_element(
            By.ID, "id_transaction_list_title"
        ).text
        self.assertIn("Transactions", transaction_list_title)
        self._set_transaction_date_range()
        self.browser.find_element(By.ID, "tab_transactions").click()
        self.check_for_row_in_table(
            [
                "UNKNOWN",
                "XX00000000000000000000",
                "Billy's transaction",
                "2022-01-01 00:00:00+00:00",
                "300.0000000",
                "UNKNOWN",
                "",
            ],
            "id_montrek_table_list",
        )

    def _set_transaction_date_range(self):
        # He then sets the time window to January 2019
        new_transaction_date_box = self.browser.find_element(
            By.ID, "id_date_range_start"
        )
        new_transaction_date_box.send_keys("01/01/2022")
        new_transaction_date_box = self.browser.find_element(By.ID, "id_date_range_end")
        new_transaction_date_box.send_keys("02/01/2022")
        self.browser.find_element(By.ID, "id_date_range_filter").click()


class BankAccountFunctionalTest(MontrekFunctionalTest):
    def setUp(self):
        super().setUp()
        CreditInstitutionStaticSatelliteFactory.create(
            credit_institution_name="Bank of Testonia"
        )
        dkb_credit_institution = CreditInstitutionStaticSatelliteFactory.create(
            credit_institution_name="DKB",
            account_upload_method="dkb",
        )
        # DKB Bank account with two transactions
        self.account_hub = AccountHubFactory()
        AccountStaticSatelliteFactory(
            hub_entity=self.account_hub, account_name="Billy's DKB account"
        )
        transaction_hubs = [
            TransactionHubFactory(accounts=[self.account_hub]) for _ in range(3)
        ]
        self.transaction_satellite_1 = TransactionSatelliteFactory(
            hub_entity=transaction_hubs[0],
            transaction_date=timezone.datetime(2019, 1, 1),
            transaction_amount=7051,
            transaction_price=101.2,
            transaction_party="Testonia",
            transaction_party_iban="XX123456789",
            transaction_description="Test transaction 1",
        )
        self.transaction_satellite_2 = TransactionSatelliteFactory(
            hub_entity=transaction_hubs[1],
            transaction_date=timezone.datetime(2019, 1, 15),
            transaction_amount=2000,
            transaction_price=98.2,
            transaction_party="Testosteria",
            transaction_party_iban="XY987654321",
            transaction_description="Test transaction 2",
        )
        self.transaction_satellite_3 = TransactionSatelliteFactory(
            hub_entity=transaction_hubs[2],
            transaction_date=timezone.datetime(2019, 1, 17),
            transaction_amount=1,
            transaction_price=78.2,
            transaction_party="Another Company",
            transaction_party_iban="XY754372638",
            transaction_description="Test transaction 3",
        )
        BankAccountPropertySatelliteFactory(hub_entity=self.account_hub)
        BankAccountStaticSatelliteFactory(hub_entity=self.account_hub)
        self.account_hub.link_account_credit_institution.add(
            dkb_credit_institution.hub_entity
        )

    @tag("functional")
    def test_add_bank_account(self):
        # The user visits the new account form
        self.browser.get(self.live_server_url + "/account/new_form")
        # The page title is 'Montrek'
        self.assertIn("Montrek", self.browser.title)
        # The header line says 'Add new Account'
        header_text = self.browser.find_element(By.TAG_NAME, "h1").text
        self.assertIn("Add new Account", header_text)
        # He enters 'Billy's account' into the Account Name Box
        new_account_name_box = self.browser.find_element(By.ID, "id_account_new__name")
        new_account_name_box.send_keys("Billy's Bank account")
        # he selects 'Bank Account' from the Account Type dropdown
        new_account_type_box = self.browser.find_element(
            By.ID, "id_account_new__account_type"
        )
        new_account_type_box.send_keys("Bank Account")
        # When he hits the submit button, he is directed to the new bank
        # account form
        self.browser.find_element(By.ID, "id_account_new__submit").click()
        header_text = self.browser.find_element(By.TAG_NAME, "h1").text
        self.assertIn("Add new Bank Account", header_text)
        # He enters the bank account data
        # He selects 'Bank of Testonia' from the credit institution dropdown
        new_account_credit_institution_box = self.browser.find_element(
            By.ID, "id_bank_account_new__credit_institution"
        )
        new_account_credit_institution_box.send_keys("Bank of Testonia")
        # He enters his IBAN in the IBAN box
        new_account_iban_box = self.browser.find_element(
            By.ID, "id_bank_account_new__iban"
        )
        new_account_iban_box.send_keys("DE12345678901234567890")

        # When he hits the submit button, he is directed to the accounts-list,
        # where he finds his new account listed
        self.browser.find_element(By.ID, "id_bank_account_new__submit").click()
        header_text = self.browser.find_element(By.ID, "id_tab_account_list").text
        self.assertIn("Account List", header_text)
        self.check_for_row_in_table(["Billy's Bank account"], "id_montrek_table_list")
        first_id = self.find_object_hub_id(
            AccountStaticSatellite, "Billy's Bank account", "account_name"
        )
        self.browser.find_element(By.ID, f"id__account_{first_id}_view").click()
        header_text = self.browser.find_element(By.ID, "id_account_details_title").text
        self.assertIn("Bank Account Details", header_text)
        self.check_for_row_in_table(
            ["Billy's Bank account", "Bank of Testonia", "DE12345678901234567890"],
            "id_account_details",
        )

    @tag("functional")
    def test_transaction_view(self):
        # Steve looks at his account and navigates to the transaction view
        self.browser.get(
            self.live_server_url + f"/account/{self.account_hub.id}/bank_account_view"
        )
        self.browser.find_element(By.ID, "tab_transactions").click()
        # At first he does not see any transactions, since the last ones were in 2019
        # (The header row does not count)
        transactions_list = self.browser.find_element(By.ID, "id_montrek_table_list")
        rows_count = len(transactions_list.find_elements(By.TAG_NAME, "tr")) - 1
        self.assertEqual(rows_count, 0)
        self._set_transaction_date_range()
        # He now finds two transactions listed
        transactions_list = self.browser.find_element(By.ID, "id_montrek_table_list")
        rows_count = len(transactions_list.find_elements(By.TAG_NAME, "tr")) - 1
        self.assertEqual(rows_count, 3)
        # He clicks on the transaction view of the first transaction
        self.browser.find_element(
            By.ID, f"id__transaction_{self.transaction_satellite_1.id}_view_"
        ).click()
        # He finds all the necessary information
        self.assertEqual(
            self.browser.find_element(By.ID, "id_transaction_date").get_attribute(
                "value"
            ),
            "2019-01-01 00:00:00",
        )
        self.assertEqual(
            self.browser.find_element(By.ID, "id_transaction_amount").get_attribute(
                "value"
            ),
            "7051.00000",
        )
        self.assertEqual(
            self.browser.find_element(By.ID, "id_transaction_price").get_attribute(
                "value"
            ),
            "101.20",
        )
        self.assertEqual(
            self.browser.find_element(By.ID, "id_transaction_party").get_attribute(
                "value"
            ),
            "Testonia",
        )
        self.assertEqual(
            self.browser.find_element(
                By.ID, "id_transaction_description"
            ).get_attribute("value"),
            "Test transaction 1",
        )

    @tag("functional")
    def test_dkb_transactions_upload(self):
        # The user visits the bank account page
        account_id = get_hub_ids_by_satellite_attribute(
            AccountStaticSatellite, "account_name", "Billy's DKB account"
        )[0]
        self.browser.get(
            self.live_server_url
            + f"/account/{account_id}/bank_account_view/transactions"
        )
        header_text = self.browser.find_element(By.TAG_NAME, "h1").text
        self.assertIn("Billy's DKB account", header_text)
        # He has two transactions listed
        self.browser.find_element(By.ID, "tab_transactions").click()
        self._set_transaction_date_range()
        transactions_list = self.browser.find_element(By.ID, "id_montrek_table_list")
        rows_count = len(transactions_list.find_elements(By.TAG_NAME, "tr"))
        assert rows_count - 1 == 3
        # He goes to the upload tab
        self.browser.find_element(By.ID, "tab_uploads").click()
        # Here he finds a link to upload DKB transactions
        self.browser.find_element(By.ID, "id_transactions_upload").click()
        # He is directed to the upload form
        header_text = self.browser.find_element(By.TAG_NAME, "h1").text
        self.assertIn("Upload Transaction File To Account", header_text)
        # He selects the file to upload
        file_upload_box = self.browser.find_element(
            By.ID, "id_dkb_transactions_upload__file"
        )
        file_upload_box.send_keys(
            os.path.join(
                os.path.dirname(__file__),
                "data/test_dkb_data.csv",
            )
        )
        # When he hits the submit button, he is directed to a upload summary page
        self.browser.find_element(By.ID, "id_dkb_transactions_upload__submit").click()
        header_text = self.browser.find_element(By.TAG_NAME, "h1").text
        self.assertIn("Upload File Result", header_text)
        # He sees that the upload was successful
        message_text = self.browser.find_element(
            By.ID, "id_upload_message_success"
        ).text
        self.assertIn("DKB upload was successful!", message_text)
        # He sees that two transactions were added
        # TODO: check for the actual transactions
        # HE hits the back button and is directed to the account page
        self.browser.find_element(By.ID, "id_back_button").click()
        header_text = self.browser.find_element(By.TAG_NAME, "h1").text
        self.assertIn("Billy's DKB account", header_text)

    @tag("functional")
    def test_add_transaction_cateogry_via_table(self):
        # The user visits the bank account transaction category map page
        account_id = get_hub_ids_by_satellite_attribute(
            AccountStaticSatellite, "account_name", "Billy's DKB account"
        )[0]
        self.browser.get(
            self.live_server_url
            + f"/account/{account_id}/bank_account_view/transaction_category_map"
        )
        # He hits the add button
        self.browser.find_element(By.ID, "id_add_transaction_category").click()
        # He fills in the form
        self.browser.find_element(
            By.ID, "id_transaction_category_new__field"
        ).send_keys("transaction_iban")
        self.browser.find_element(
            By.ID, "id_transaction_category_new__value"
        ).send_keys("XY754372638")
        self.browser.find_element(
            By.ID, "id_transaction_category_new__category"
        ).send_keys("TESTCATEGORY")
        # He hits the submit button
        self.browser.find_element(By.ID, "id_transaction_category_new__submit").click()
        transactions_category_map_list = self.browser.find_element(
            By.ID, "id_montrek_table_list"
        )
        rows_count = len(
            transactions_category_map_list.find_elements(By.TAG_NAME, "tr")
        )
        assert rows_count - 1 == 1
        self.check_for_row_in_table(
            ["transaction_party_iban", "XY754372638", "TESTCATEGORY"],
            "id_montrek_table_list",
        )
        # He checks the transaction view and sees that the category is set
        self.browser.find_element(By.ID, "tab_transactions").click()
        self._set_transaction_date_range()
        self.browser.find_element(
            By.ID, f"id__transaction_{self.transaction_satellite_3.id}_view_"
        ).click()
        self.assertEqual(
            self.browser.find_element(By.ID, "id_transaction_category").text,
            "TESTCATEGORY",
        )

    @tag("functional")
    def test_add_transaction_cateogry_via_table_regex(self):
        # The user visits the bank account transaction category map page
        account_id = get_hub_ids_by_satellite_attribute(
            AccountStaticSatellite, "account_name", "Billy's DKB account"
        )[0]
        self.browser.get(
            self.live_server_url
            + f"/account/{account_id}/bank_account_view/transaction_category_map"
        )
        # He hits the add button
        self.browser.find_element(By.ID, "id_add_transaction_category").click()
        self.browser.find_element(
            By.ID, "id_transaction_category_new__value"
        ).send_keys("Test")
        self.browser.find_element(
            By.ID, "id_transaction_category_new__category"
        ).send_keys("SUPERTESTCATEGORY")
        self.browser.find_element(By.ID, "id_transaction_category_new__regex").click()
        # He hits the submit button
        self.browser.find_element(By.ID, "id_transaction_category_new__submit").click()
        self.check_for_row_in_table(
            ["transaction_party", "Test", "SUPERTESTCATEGORY", "True"],
            "id_montrek_table_list",
        )
        self.browser.find_element(By.ID, "tab_transactions").click()
        self._set_transaction_date_range()
        self.check_for_row_in_table(
            ["Testonia", "SUPERTESTCATEGORY"],
            "id_montrek_table_list",
        )
        self.check_for_row_in_table(
            ["Testosteria", "SUPERTESTCATEGORY"],
            "id_montrek_table_list",
        )

    @tag("functional")
    def test_change_transaction_category_from_transaction_table(self):
        # The user visits the bank account transaction page
        account_id = get_hub_ids_by_satellite_attribute(
            AccountStaticSatellite, "account_name", "Billy's DKB account"
        )[0]
        self.browser.get(
            self.live_server_url
            + f"/account/{account_id}/bank_account_view/transactions"
        )
        self._set_transaction_date_range()
        # He clicks on the category edit for counterparty botton
        self.browser.find_element(
            By.ID,
            f"id__transaction_add_transaction_category_{account_id}_cp_Another%20Company",
        ).click()
        # He sets the category to 'TESTCATEGORY'
        self.browser.find_element(
            By.ID, "id_transaction_category_new__category"
        ).send_keys("TESTCATEGORY")
        self.browser.find_element(By.ID, "id_transaction_category_new__submit").click()
        # He finds the category in the table
        self.check_for_row_in_table(
            ["transaction_party", "Another Company", "TESTCATEGORY"],
            "id_montrek_table_list",
        )
        self.browser.find_element(By.ID, "tab_transactions").click()
        # He checks the transaction view and sees that the category is set
        self.browser.find_element(
            By.ID, f"id__transaction_{self.transaction_satellite_3.id}_view_"
        ).click()
        self.assertEqual(
            self.browser.find_element(By.ID, "id_transaction_category").text,
            "TESTCATEGORY",
        )

        # He goes back to the transactio table
        self.browser.find_element(By.ID, "id_back").click()

        # Now he changes the category for the second transaction based on the IBAN
        self.browser.find_element(
            By.ID,
            f"id__transaction_add_transaction_category_{account_id}_iban_XY987654321",
        ).click()
        # He sets the category to 'TESTCATEGORY'
        self.browser.find_element(
            By.ID, "id_transaction_category_new__category"
        ).send_keys("TESTCATEGORY 2")
        self.browser.find_element(By.ID, "id_transaction_category_new__submit").click()
        # He finds the category in the table
        self.check_for_row_in_table(
            ["transaction_party_iban", "XY987654321", "TESTCATEGORY 2"],
            "id_montrek_table_list",
        )
        self.browser.find_element(By.ID, "tab_transactions").click()
        # He checks the transaction view and sees that the category is set
        self.browser.find_element(
            By.ID, f"id__transaction_{self.transaction_satellite_2.id}_view_"
        ).click()
        self.assertEqual(
            self.browser.find_element(By.ID, "id_transaction_category").text,
            "TESTCATEGORY2",
        )

        # He goes back to the transactio table
        self.browser.find_element(By.ID, "id_back").click()

    def _set_transaction_date_range(self):
        # He then sets the time window to January 2019
        new_transaction_date_box = self.browser.find_element(
            By.ID, "id_date_range_start"
        )
        new_transaction_date_box.send_keys("01/01/2019")
        new_transaction_date_box = self.browser.find_element(By.ID, "id_date_range_end")
        new_transaction_date_box.send_keys("02/01/2019")
        self.browser.find_element(By.ID, "id_date_range_filter").click()


class TestDepotAccount(MontrekFunctionalTest):
    def setUp(self):
        super().setUp()
        CreditInstitutionStaticSatelliteFactory.create(
            credit_institution_name="Bank of Testonia"
        )

    @tag("functional")
    @patch("asset.managers.market_data.yf.download")
    def test_add_depot_and_add_asset_transactions(self, mock_download):
        mock_data_df = self._get_yf_prices_mock_data()
        mock_download.return_value = mock_data_df
        # The user visits the new account form
        self.browser.get(self.live_server_url + "/account/new_form")
        # He enters 'Billy's Depot account' into the Account Name Box
        new_account_name_box = self.browser.find_element(By.ID, "id_account_new__name")
        new_account_name_box.send_keys("Billy's Depot")
        # he selects 'Depot' from the Account Type dropdown
        new_account_type_box = self.browser.find_element(
            By.ID, "id_account_new__account_type"
        )
        new_account_type_box.send_keys("Depot")
        self.browser.find_element(By.ID, "id_account_new__submit").click()
        header_text = self.browser.find_element(By.TAG_NAME, "h1").text
        self.assertIn("Add new Depot", header_text)
        # He enters the bank account data
        # He selects 'Bank of Testonia' from the credit institution dropdown
        new_account_credit_institution_box = self.browser.find_element(
            By.ID, "id_bank_account_new__credit_institution"
        )
        new_account_credit_institution_box.send_keys("Bank of Testonia")
        # He enters his IBAN in the IBAN box
        new_account_iban_box = self.browser.find_element(
            By.ID, "id_bank_account_new__iban"
        )
        new_account_iban_box.send_keys("DE12345678901234567890")

        # When he hits the submit button, he is directed to the accounts-list,
        # where he finds his new account listed
        self.browser.find_element(By.ID, "id_bank_account_new__submit").click()
        header_text = self.browser.find_element(By.ID, "id_tab_account_list").text
        self.assertIn("Account List", header_text)
        self.check_for_row_in_table(["Billy's Depot"], "id_montrek_table_list")

        # He clicks on the account link in the list
        account_id = self.find_object_hub_id(
            AccountStaticSatellite, "Billy's Depot", "account_name"
        )
        self.browser.find_element(By.ID, f"id__account_{account_id}_view").click()

        # He finds the depot tab and clicks on it
        header_text = self.browser.find_element(By.ID, "tab_depot").text
        self.assertIn("Depot", header_text)
        self.browser.find_element(By.ID, "tab_depot").click()
        # There he finds an empty list of assets
        asset_list = self.browser.find_element(By.ID, "id_montrek_table_list")
        rows_count = len(asset_list.find_elements(By.TAG_NAME, "tr")) - 1
        self.assertEqual(rows_count, 0)
        # He adds an transaction with an asset
        self.browser.find_element(By.ID, "tab_transactions").click()
        self.browser.find_element(By.ID, "add_transaction").click()
        # Since there are not assets yet, he adds one
        self.browser.find_element(By.ID, "id_add_new_asset").click()
        header_text = self.browser.find_element(By.ID, "id_title").text
        self.assertIn("Create Asset Static", header_text)
        # He enters the asset data
        for page_id, value in [
            ("id_asset_name", "Test Asset"),
            ("id_asset_type", "ETF"),
        ]:
            self.browser.find_element(By.ID, page_id).send_keys(value)
        # He hits the submit button and is asked to enter liquid asset data
        self.browser.find_element(By.ID, "id_submit").click()
        header_text = self.browser.find_element(By.ID, "id_title").text
        self.assertIn("Create Asset Liquid", header_text)
        for page_id, value in [
            ("id_asset_isin", "DE12345678910"),
            ("id_asset_wkn", "ETF001"),
        ]:
            self.browser.find_element(By.ID, page_id).send_keys(value)
        self.browser.find_element(By.ID, "id_submit").click()
        # He is directed back to the transaction form and finds his asset in the selection box
        asset_name = self.browser.find_element(By.ID, "id_transaction_new__asset").text
        self.assertIn("Test Asset", asset_name)
        # He enters the transaction data
        new_transaction_name_box = self.browser.find_element(
            By.ID, "id_transaction_new__name"
        )
        new_transaction_name_box.send_keys("Billy's transaction")
        new_transaction_amount_box = self.browser.find_element(
            By.ID, "id_transaction_new__amount"
        )
        new_transaction_amount_box.send_keys("3")
        new_transaction_price_box = self.browser.find_element(
            By.ID, "id_transaction_new__price"
        )
        new_transaction_price_box.send_keys("100.00")
        new_transaction_date_box = self.browser.find_element(
            By.ID, "id_transaction_new__date"
        )
        new_transaction_date_box.send_keys("01/01/2022")
        test_asset_id = self.find_object_hub_id(
            AssetStaticSatellite, "Test Asset", "asset_name"
        )
        self.browser.find_element(By.ID, "id_transaction_new__asset").send_keys(
            f"Test Asset (ETF) <{test_asset_id}>"
        )
        # He submits and finds himself in the depot view
        self.browser.find_element(By.ID, "id_transaction_new__submit").click()
        self._set_transaction_date_range()
        asset_list = self.browser.find_element(By.ID, "id_montrek_table_list")
        rows_count = len(asset_list.find_elements(By.TAG_NAME, "tr")) - 1
        self.assertEqual(rows_count, 1)
        self.check_for_row_in_table(
            ["Test Asset", "Billy's transaction", "300.0000000"],
            "id_montrek_table_list",
        )
        # Check the Depot Table
        self.browser.find_element(By.ID, "tab_depot").click()
        self.check_for_row_in_table(
            ["Test Asset", "DE1234567891", "ETF001", "3.00", "100.00", "300.00"],
            "id_montrek_table_list",
        )
        # Refresh the prices
        self.browser.find_element(By.ID, "id_update_asset_prices").click()
        self.check_for_row_in_table(
            [
                "Test Asset",
                "DE1234567891",
                "ETF001",
                "3.00",
                "100.00",
                "300.00",
                "5.94",
                "17.82",
                "2022-02-01",
                "-94.06%",
            ],
            "id_montrek_table_list",
        )

    def _set_transaction_date_range(self):
        # He then sets the time window to January 2022
        new_transaction_date_box = self.browser.find_element(
            By.ID, "id_date_range_start"
        )
        new_transaction_date_box.send_keys("01/01/2022")
        new_transaction_date_box = self.browser.find_element(By.ID, "id_date_range_end")
        new_transaction_date_box.send_keys("02/01/2022")
        self.browser.find_element(By.ID, "id_date_range_filter").click()

    def _get_yf_prices_mock_data(self):
        data = {
            "Adj Close": [5.9425],
            "Close": [5.9425],
            "High": [5.9575],
            "Low": [5.905],
            "Open": [5.905],
            "Volume": [9316.0],
        }

        index = pd.DatetimeIndex(["2022-02-01"], name="Date")
        return pd.DataFrame(data, index=index)
