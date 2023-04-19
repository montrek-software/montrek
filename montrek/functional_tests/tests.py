from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, NoSuchElementException
import time
import unittest

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
    def check_for_row_in_table(self, row_text, table_id):
        table = self.browser.find_element(By.ID, table_id)
        rows = table.find_elements(By.TAG_NAME,'td')
        self.assertIn(row_text, [row.text for row in rows])

class AccountFunctionalTests(MontrekFunctionalTest):

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
        self.check_for_row_in_table('Billy\'s account', 'id_account_list')

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
        self.browser.find_element(By.ID, 'link_account_1').click()
        # The name of the Account is shown in the header
        header_text = self.browser.find_element(By.TAG_NAME,'h1').text
        self.assertIn('Billy\'s account', header_text)
        # After clicking on the back button he is back at the list
        self.browser.find_element(By.ID, 'list_back').click()
        header_text = self.browser.find_element(By.TAG_NAME,'h1').text
        self.assertIn('Account List', header_text)
        # He clicks on the second link and finds the account's name
        self.browser.find_element(By.ID, 'link_account_2').click()
        # The name of the Account is shown in the header
        header_text = self.browser.find_element(By.TAG_NAME,'h1').text
        self.assertIn('Billy\'s second account', header_text)
        # After clicking on the back button he is back at the list
        self.browser.find_element(By.ID, 'list_back').click()
        header_text = self.browser.find_element(By.TAG_NAME,'h1').text
        self.assertIn('Account List', header_text)




