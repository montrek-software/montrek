import os
import time
from typing import List
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
        satellite_object = get_hub_ids_by_satellite_attribute(
            satellite_model, object_field, object_name
        )[0]
        return satellite_object


class AccountFunctionalTests(MontrekFunctionalTest):
    @tag("functional")
    def test_add_new_account(self):
        # The user visits the new account form
        self.browser.get(self.live_server_url + "/account/new_form")
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
        self.browser.find_element(
            By.ID, "id_account_new__submit"
        ).click()
        header_text = self.browser.find_element(By.TAG_NAME, "h1").text
        self.assertIn("Account List", header_text)
        self.check_for_row_in_table(["Billy's account"], "id_list")

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
        self.browser.find_element(By.ID, f"link_{first_id}").click()
        # The name of the Account is shown in the header
        header_text = self.browser.find_element(By.ID, "page_title").text
        self.assertIn("Billy's account", header_text)
        # After clicking on the back button he is back at the list
        self.browser.find_element(By.ID, "list_back").click()
        header_text = self.browser.find_element(By.TAG_NAME, "h1").text
        self.assertIn("Account List", header_text)
        # He clicks on the second link and finds the account's name
        second_id = self.find_object_hub_id(
            AccountStaticSatellite, "Billy's second account", "account_name"
        )
        self.browser.find_element(By.ID, f"link_{second_id}").click()
        # The name of the Account is shown in the header
        header_text = self.browser.find_element(By.TAG_NAME, "h1").text
        self.assertIn("Billy's second account", header_text)
        # After clicking on the back button he is back at the list
        self.browser.find_element(By.ID, "list_back").click()
        header_text = self.browser.find_element(By.TAG_NAME, "h1").text
        self.assertIn("Account List", header_text)
        # He now wants to delete the first account
        self.browser.find_element(By.ID, f"link_{first_id}").click()
        # He clicks on the delete button
        self.browser.find_element(By.ID, "delete_account").click()
        # He is asked to confirm the deletion
        header_text = self.browser.find_element(By.TAG_NAME, "h1").text
        self.assertIn("Delete Account", header_text)
        # He clicks on the delete button
        self.browser.find_element(By.ID, "delete_account").click()
        # He is back at the list and the first account is gone
        header_text = self.browser.find_element(By.TAG_NAME, "h1").text
        self.assertIn("Account List", header_text)
        self.check_for_row_in_table(["Billy's second account"], "id_list")
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
        self.browser.find_element(By.ID, "tab_transactions").click()
        self.check_for_row_in_table(
            ['NONE', 'XX00000000000000000000', "Billy's transaction",
             'Jan. 1, 2022, midnight', '300.00', 'UNKNOWN', ''],
            "id_montrek_table_list",
        )


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
        transaction_hub = TransactionHubFactory()
        self.transaction_satellite_1 = TransactionSatelliteFactory(
            hub_entity=transaction_hub,
            transaction_date=timezone.datetime(2019, 1, 1),
        )
        self.transaction_satellite_2 = TransactionSatelliteFactory(
            hub_entity=transaction_hub
        )
        self.account_hub.link_account_transaction.add(transaction_hub)
        BankAccountPropertySatelliteFactory(
            hub_entity=self.account_hub
        )
        BankAccountStaticSatelliteFactory(
            hub_entity=self.account_hub
        )
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
        self.browser.find_element(
            By.ID, "id_account_new__submit"
        ).click()
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
        self.browser.find_element(
            By.ID, "id_bank_account_new__submit"
        ).click()
        header_text = self.browser.find_element(By.TAG_NAME, "h1").text
        self.assertIn("Account List", header_text)
        self.check_for_row_in_table(["Billy's Bank account"], "id_list")
        first_id = self.find_object_hub_id(
            AccountStaticSatellite, "Billy's Bank account", "account_name"
        )
        self.browser.find_element(By.ID, f"link_{first_id}").click()
        header_text = self.browser.find_element(By.ID, "id_account_details_title").text
        self.assertIn("Bank Account Details", header_text)
        self.check_for_row_in_table(
            ["Billy's Bank account", "Bank of Testonia", "DE12345678901234567890"],
            "id_account_details",
        )

    @tag("functional")
    def test_transaction_view(self):
        #Steve looks at his account and navigates to the transaction view
        self.browser.get(self.live_server_url + f"/account/{self.account_hub.id}/bank_account_view")
        self.browser.find_element(By.ID, "tab_transactions").click()
        # He clicks on the transaction view of the first transaction
        self.browser.find_element(
            By.ID,
            f"id__transaction_{self.transaction_satellite_1.hub_entity.id}_view_"
        ).click()
        # He finds all the necessary information
        self.assertEqual(self.browser.find_element(By.ID, "id_transaction_date").get_attribute('value'), "2019-01-01 00:00:00")
        return
        self.assertEqual(self.browser.find_element(By.ID, "id_transaction_details__amount").text, "100.00")
        self.assertEqual(self.browser.find_element(By.ID, "id_transaction_details__price").text, "1.00")
        self.assertEqual(self.browser.find_element(By.ID, "id_transaction_details__party").text, "Testonia")
        self.assertEqual(self.browser.find_element(By.ID, "id_transaction_details__description").text, "Test transaction 1")

    @tag("functional")
    def test_dkb_transactions_upload(self):
        # The user visits the bank account page
        account_id = get_hub_ids_by_satellite_attribute(
            AccountStaticSatellite, "account_name", "Billy's DKB account"
        )[0]
        self.browser.get(
            self.live_server_url + f"/account/{account_id}/bank_account_view/transactions"
        )
        header_text = self.browser.find_element(By.TAG_NAME, "h1").text
        self.assertIn("Billy's DKB account", header_text)
        # He has two transactions listed
        self.browser.find_element(By.ID, "tab_transactions").click()
        transactions_list = self.browser.find_element(By.ID, "id_montrek_table_list")
        rows_count = len(transactions_list.find_elements(By.TAG_NAME, "tr"))
        assert rows_count - 1 == 2
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
        self.browser.find_element(
            By.ID, "id_dkb_transactions_upload__submit"
        ).click()
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
