import os
import pandas as pd

from django.test import TestCase

from account.tests.factories.account_factories import BankAccountStaticSatelliteFactory
from account.tests.factories.account_factories import AccountStaticSatelliteFactory
from credit_institution.tests.factories.credit_institution_factories import CreditInstitutionStaticSatelliteFactory
from link_tables.tests.factories.link_tables_factories import AccountCreditInstitutionLinkFactory

from account.managers.transaction_upload_methods import upload_dkb_transactions
from account.managers.transaction_upload_methods import read_dkb_transactions_from_csv

class TestDKBTransactionUpload(TestCase):
    test_csv_path = os.path.join(os.path.dirname(__file__), 'data/dkb_test.csv')
    @classmethod
    def setUpTestData(cls):
       cls.bank_account = BankAccountStaticSatelliteFactory.create()
       AccountStaticSatelliteFactory.create(
           hub_entity=cls.bank_account.hub_entity,
           account_type='BankAccount',)
       cls.credit_institution = CreditInstitutionStaticSatelliteFactory.create()
       AccountCreditInstitutionLinkFactory.create(
           from_hub=cls.bank_account.hub_entity,
           to_hub=cls.credit_institution.hub_entity,
       )

    def test_check_if_upload_method_is_dkb(self):
        with self.assertRaises(AttributeError) as e:
            upload_dkb_transactions(self.bank_account.hub_entity, '')
        self.assertEqual(str(e.exception), 'Account Upload Method is not of type dkb')

    def test_read_dkb_transactions(self):
        test_df = read_dkb_transactions_from_csv(self.test_csv_path)
        breakpoint()
        self.assertTrue(isinstance(test_df, pd.DataFrame))
