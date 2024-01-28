import os
from django.test import TestCase
from account.managers.account_file_upload_manager import AccountFileUploadProcessor
from account.tests.factories.account_factories import AccountHubFactory
from credit_institution.tests.factories.credit_institution_factories import CreditInstitutionStaticSatelliteFactory

class TestAccountFileUploadManager(TestCase):
    test_csv_path = os.path.join(os.path.dirname(__file__), "data/dkb_test.csv")
    def setUp(self):
        self.account_hub = AccountHubFactory()
        self.credit_institution_sat = CreditInstitutionStaticSatelliteFactory(
            account_upload_method="dkb",
        )
        self.account_hub.link_account_credit_institution.add(self.credit_institution_sat.hub_entity)

    def test_process(self):
        account_file_upload_processor = AccountFileUploadProcessor(
            **{'pk': self.account_hub.pk}
        )
        result = account_file_upload_processor.process(self.test_csv_path)
        self.assertEqual(account_file_upload_processor.message, "DKB upload was successful")
        self.assertEqual(result, True)
