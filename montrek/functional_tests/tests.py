from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import tag
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, NoSuchElementException
import time
import unittest
from typing import List

from account.models import AccountStaticSatellite
from baseclasses.models import MontrekSatelliteABC
from account.tests.factories import account_factories
from baseclasses.model_utils import get_hub_ids_by_satellite_attribute

MAX_WAIT = 10

class MontrekFunctionalTest(StaticLiveServerTestCase):


    def setUp(self):
        try:
            self.browser = webdriver.Chrome()
        except WebDriverException:
            self.browser = webdriver.Chrome('/usr/bin/chromedriver')

    def tearDown(self):
        self.browser.quit()

    def wait_for_browser_action(browser_action):
        def inner_function(*args, **kwargs):
            start_time = time.time()
            while True:
                try:
                    browser_action(*args, **kwargs)
                    return
                except (AssertionError, WebDriverException) as e:
                    if time.time() - start_time > MAX_WAIT:
                        raise e
                    time.sleep(0.5)
        return inner_function

    @wait_for_browser_action
    def check_for_row_in_table(self, row_content:List[str], table_id:str):
        table = self.browser.find_element(By.ID, table_id)
        rows = table.find_elements(By.TAG_NAME,'td')
        for row_text in row_content:
            self.assertIn(row_text, [row.text for row in rows])

    def find_object_hub_id(self, satellite_model: MontrekSatelliteABC, 
                           object_name: str, 
                           object_field: str):
        # Since the table ids depend on what has been in the DB before the test
        # ran, we need to find the id of the object we are looking for
        satellite_object = get_hub_ids_by_satellite_attribute(satellite_model, 
                                                              object_field,
                                           object_name)[0]
        return satellite_object

class AccountFunctionalTests(MontrekFunctionalTest):

    @tag('functional')
    def test_add_new_account(self):
        # The user visits the new account form
        self.browser.get(self.live_server_url + '/account/new_form')
        # The page title is 'Montrek'
        self.assertIn('Montrek', self.browser.title)
        # The header line says 'Add new Account'
        header_text = self.browser.find_element(By.TAG_NAME,'h1').text
        self.assertIn('Add new Account', header_text)
        # He enters 'Billy's account' into the Account Name Box
        new_account_name_box = self.browser.find_element(By.ID,
            'id_account_new__name')
        new_account_name_box.send_keys('Billy\'s account')
        # When he hits the submit button, he is directed to the accounts-list,
        # where he finds his new account listed
        new_list_submit = self.browser.find_element(By.ID,
                                                    'id_account_new__submit').click()
        header_text = self.browser.find_element(By.TAG_NAME,'h1').text
        self.assertIn('Account List', header_text)
        self.check_for_row_in_table(['Billy\'s account'], 'id_list')

    @tag('functional')
    def test_access_account_in_list(self):
        # The user sets up two new accounts
        self.browser.get(self.live_server_url + '/account/new_form')
        new_account_name_box = self.browser.find_element(By.ID,
            'id_account_new__name')
        new_account_name_box.send_keys('Billy\'s account')
        self.browser.find_element(By.ID, 'id_account_new__submit').click()
        self.browser.get(self.live_server_url + '/account/new_form')
        new_account_name_box = self.browser.find_element(By.ID,
            'id_account_new__name')
        new_account_name_box.send_keys('Billy\'s second account')
        self.browser.find_element(By.ID, 'id_account_new__submit').click()
        # He clicks on the first account link in the list
        first_id = self.find_object_hub_id(AccountStaticSatellite, 
                                           'Billy\'s account',
                                          'account_name')
        self.browser.find_element(By.ID, f'link_{first_id}').click()
        # The name of the Account is shown in the header
        header_text = self.browser.find_element(By.TAG_NAME,'h1').text
        self.assertIn('Billy\'s account', header_text)
        # After clicking on the back button he is back at the list
        self.browser.find_element(By.ID, 'list_back').click()
        header_text = self.browser.find_element(By.TAG_NAME,'h1').text
        self.assertIn('Account List', header_text)
        # He clicks on the second link and finds the account's name
        second_id = self.find_object_hub_id(AccountStaticSatellite, 
                                           'Billy\'s second account',
                                          'account_name')
        self.browser.find_element(By.ID, f'link_{second_id}').click()
        # The name of the Account is shown in the header
        header_text = self.browser.find_element(By.TAG_NAME,'h1').text
        self.assertIn('Billy\'s second account', header_text)
        # After clicking on the back button he is back at the list
        self.browser.find_element(By.ID, 'list_back').click()
        header_text = self.browser.find_element(By.TAG_NAME,'h1').text
        self.assertIn('Account List', header_text)
        # He now wants to delete the first account
        self.browser.find_element(By.ID, f'link_{first_id}').click()
        # He clicks on the delete button
        self.browser.find_element(By.ID, 'delete_account').click()
        # He is asked to confirm the deletion
        header_text = self.browser.find_element(By.TAG_NAME,'h1').text
        self.assertIn('Delete Account', header_text)
        # He clicks on the delete button
        self.browser.find_element(By.ID, 'delete_account').click()
        # He is back at the list and the first account is gone
        header_text = self.browser.find_element(By.TAG_NAME,'h1').text
        self.assertIn('Account List', header_text)
        self.check_for_row_in_table(['Billy\'s second account'], 'id_list')
        self.assertNotIn('Billy\'s account', self.browser.page_source)


class TransactionFunctionalTest(MontrekFunctionalTest):
    @classmethod
    def setUp(cls):
        account_factories.AccountStaticSatelliteFactory.create_batch(1)
        super().setUp(cls)

    @tag('functional')
    def test_add_transaction_to_account(self):
        last_account_name = AccountStaticSatellite.objects.last().account_name
        account_id = self.find_object_hub_id(AccountStaticSatellite,
                                             last_account_name,
                                            'account_name')
        #The user visists the account page
        self.browser.get(self.live_server_url + f'/account/{account_id}/view')
        # He clicks on the add transaction button
        self.browser.find_element(By.ID, 'add_transaction').click()
        # He is directed to the transaction form
        header_text = self.browser.find_element(By.TAG_NAME,'h1').text
        self.assertIn(f'Add transaction to {last_account_name}', header_text)
        # He enters the transaction data
        new_transaction_name_box = self.browser.find_element(By.ID,
            'id_transaction_new__name')
        new_transaction_name_box.send_keys('Billy\'s transaction')
        new_transaction_amount_box = self.browser.find_element(By.ID,
            'id_transaction_new__amount')
        new_transaction_amount_box.send_keys('3')
        new_transaction_price_box = self.browser.find_element(By.ID,
            'id_transaction_new__price')
        new_transaction_price_box.send_keys('100.00')
        new_transaction_date_box = self.browser.find_element(By.ID,
            'id_transaction_new__date')
        new_transaction_date_box.send_keys('01/01/2022')
        # He hits the submit button
        self.browser.find_element(By.ID, 'id_transaction_new__submit').click()
        # He is directed back to the account page
        header_text = self.browser.find_element(By.TAG_NAME,'h1').text
        self.assertIn(last_account_name, header_text)
        # He sees the new transaction in the list
        transaction_list_title = self.browser.find_element(By.ID,'id_transaction_list_title').text
        self.assertIn('Transactions', transaction_list_title)
        self.check_for_row_in_table(['Billy\'s transaction', '100.00', '3',
                                     '300.00',
                                     'Jan. 1, 2022, midnight'],
                                     'id_transaction_list')

class BankAccountFunctionalTest(MontrekFunctionalTest):
    @tag('functional')
    def test_add_bank_account(self):
        # The user visits the new account form
        self.browser.get(self.live_server_url + '/account/new_form')
        # The page title is 'Montrek'
        self.assertIn('Montrek', self.browser.title)
        # The header line says 'Add new Account'
        header_text = self.browser.find_element(By.TAG_NAME,'h1').text
        self.assertIn('Add new Account', header_text)
        # He enters 'Billy's account' into the Account Name Box
        new_account_name_box = self.browser.find_element(By.ID,
            'id_account_new__name')
        new_account_name_box.send_keys('Billy\'s Bank account')
        # he selects 'Bank Account' from the Account Type dropdown
        new_account_type_box = self.browser.find_element(By.ID,
            'id_account_new__account_type')
        new_account_type_box.send_keys('Bank Account')
        # When he hits the submit button, he is directed to the new bank
        # account form
        new_account_submit = self.browser.find_element(By.ID,
                                                    'id_account_new__submit').click()
        header_text = self.browser.find_element(By.TAG_NAME,'h1').text
        self.assertIn('Add new Bank Account', header_text)
        # He enters the bank account data
        # He selects 'Bank of Testonia' from the credit institution dropdown
        new_account_credit_institution_box = self.browser.find_element(By.ID,
            'id_bank_account_new__credit_institution')
        new_account_credit_institution_box.send_keys('Bank of Testonia')

        # When he hits the submit button, he is directed to the accounts-list,
        # where he finds his new account listed
        new_list_submit = self.browser.find_element(By.ID,
                                                    'id_bank_account_new__submit').click()
        header_text = self.browser.find_element(By.TAG_NAME,'h1').text
        self.assertIn('Account List', header_text)
        self.check_for_row_in_table(['Billy\'s Bank account'], 'id_list')
