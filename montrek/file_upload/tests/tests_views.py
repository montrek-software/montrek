from django.test import TestCase
from account.tests.factories.account_factories import AccountStaticSatelliteFactory
from credit_institution.tests.factories.credit_institution_factories import CreditInstitutionStaticSatelliteFactory
from link_tables.tests.factories.link_tables_factories import AccountCreditInstitutionLinkFactory
from file_upload.views import upload_transaction_to_account_file

class UploadTransactionToAccountFileViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.account_satellite = AccountStaticSatelliteFactory()
        cls.credit_institution_satellite = CreditInstitutionStaticSatelliteFactory()
        cls.account_credit_institution_link = AccountCreditInstitutionLinkFactory(
            from_hub=cls.account_satellite.hub_entity,
            to_hub=cls.credit_institution_satellite.hub_entity
        )

    def test_upload_transaction_to_account_file_view_get(self):
        account_id = self.account_satellite.hub_entity.id
        credit_institution_id = self.credit_institution_satellite.hub_entity.id
        response = self.client.get(
            f'/file_upload/upload_transaction_to_account_file/{account_id}/{credit_institution_id}/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'upload_transaction_to_account_form.html')

    def test_upload_transaction_to_account_file_view_post(self):
        account_id = self.account_satellite.hub_entity.id
        credit_institution_id = self.credit_institution_satellite.hub_entity.id
        #upload_transaction_to_account_file(
        


