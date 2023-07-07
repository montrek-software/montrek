from django.test import TestCase
from django.test import RequestFactory
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import default_storage
from account.tests.factories.account_factories import AccountStaticSatelliteFactory
from credit_institution.tests.factories.credit_institution_factories import CreditInstitutionStaticSatelliteFactory
from link_tables.tests.factories.link_tables_factories import AccountCreditInstitutionLinkFactory
from file_upload.tests.factories.file_upload_factories import FileUploadRegistryStaticSatelliteFactory
from file_upload.tests.factories.file_upload_factories import FileUploadFileStaticSatelliteFactory
from link_tables.tests.factories.link_tables_factories import FileUploadRegistryFileUploadFileLinkFactory
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
        # Create a file to upload
        txt_file_content = b'Test file content'
        cls.txt_file = SimpleUploadedFile('test_file.txt', txt_file_content)
        cls.file_registry_sat_factory = FileUploadRegistryStaticSatelliteFactory(
            file_name=cls.txt_file.name
        )
        cls.file_file_sat_factory = FileUploadFileStaticSatelliteFactory()
        file_registry_file_link_factory = FileUploadRegistryFileUploadFileLinkFactory(
            from_hub=cls.file_registry_sat_factory.hub_entity,
            to_hub=cls.file_file_sat_factory.hub_entity
        )


    def test_upload_transaction_to_account_file_view_get(self):
        account_id = self.account_satellite.hub_entity.id
        response = self.client.get(
            f'/file_upload/upload_transaction_to_account_file/{account_id}/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'upload_transaction_to_account_form.html')

    def test_upload_transaction_to_account_file_view_post(self):
        account_id = self.account_satellite.hub_entity.id

        # Create a POST request with the file
        url = reverse('upload_transaction_to_account_file', args=(account_id, ))
        data = {'file': self.txt_file}
        request_factory = RequestFactory()
        request = request_factory.post(url, data, format='multipart')
        request.FILES['file'] = self.txt_file

        # Execute the view function
        response = upload_transaction_to_account_file(request, account_id)

         # Assertions
        self.assertEqual(response.status_code, 200)  # Check if redirect


#    def test_dkb_file_upload_wrong_input_type(self):
#        self.file_registry_sat_factory.upload_status = 'pending'
#        self.file_registry_sat_factory.save()
#        self.credit_institution_satellite.account_upload_method = 'dkb'
#        self.credit_institution_satellite.save()
#        file_reg_sat = process_file(self.file_registry_sat_factory,
#                                    self.account_satellite.hub_entity.id)
#        self.assertEqual(file_reg_sat.upload_status, 'failed')
#        self.assertEqual(file_reg_sat.upload_message, 
#            f'DKB Upload expects a file of type .csv, but got {self.txt_file.name} '
#                        )    
