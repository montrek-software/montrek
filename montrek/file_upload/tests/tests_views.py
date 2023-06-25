from django.test import TestCase
from django.test import RequestFactory
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import default_storage
from account.tests.factories.account_factories import AccountStaticSatelliteFactory
from credit_institution.tests.factories.credit_institution_factories import CreditInstitutionStaticSatelliteFactory
from link_tables.tests.factories.link_tables_factories import AccountCreditInstitutionLinkFactory
from file_upload.views import upload_transaction_to_account_file
from file_upload.views import init_file_upload_registry
from file_upload.views import upload_file

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

    @classmethod
    def tearDownClass(cls):
        # Delete the test file
        if default_storage.exists('uploads/test_file.txt'):
            default_storage.delete('uploads/test_file.txt')
        super().tearDownClass()

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

        # Create a POST request with the file
        url = reverse('upload_transaction_to_account_file', args=(account_id, credit_institution_id))
        data = {'file': self.txt_file}
        request_factory = RequestFactory()
        request = request_factory.post(url, data, format='multipart')
        request.FILES['file'] = self.txt_file

        # Execute the view function
        response = upload_transaction_to_account_file(request, account_id, credit_institution_id)

         # Assertions
        self.assertEqual(response.status_code, 302)  # Check if redirect
        self.assertEqual(response.url, '/success/url/')  # Check if redirect URL is correct

    """
    def test_init_file_upload_registry(self):
        test_hub = self.account_satellite.hub_entity
        upload_registry_sat = init_file_upload_registry(self.txt_file, test_hub)
        self.assertEqual(upload_registry_sat.file_name, self.txt_file.name)
        self.assertEqual(upload_registry_sat.file_path, self.txt_file.path)
        self.assertEqual(upload_registry_sat.file_type, 'txt')
        self.assertEqual(upload_registry_sat.upload_status, 'pending')

    """

    def test_upload_file(self):
        fileuploadsatellite = upload_file(self.txt_file)
        self.assertIsNotNone(fileuploadsatellite.file)
        self.assertEqual(fileuploadsatellite.file.name,
                         'uploads/' + self.txt_file.name)
        self.assertEqual(fileuploadsatellite.file.url,
                         '/uploads/' + self.txt_file.name)
        with fileuploadsatellite.file.open():
            self.assertEqual(fileuploadsatellite.file.read(), b'Test file content')

