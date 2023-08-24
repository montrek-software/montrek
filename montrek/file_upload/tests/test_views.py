from django.test import TestCase
from django.test import RequestFactory
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import default_storage
from account.tests.factories.account_factories import AccountStaticSatelliteFactory
from credit_institution.tests.factories.credit_institution_factories import (
    CreditInstitutionStaticSatelliteFactory,
)
from file_upload.tests.factories.file_upload_factories import (
    FileUploadRegistryStaticSatelliteFactory,
)
from file_upload.tests.factories.file_upload_factories import (
    FileUploadFileStaticSatelliteFactory,
)
from file_upload.views import upload_transaction_to_account_file
from file_upload.views import download_upload_file


class UploadTransactionToAccountFileViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.account_satellite = AccountStaticSatelliteFactory()
        cls.credit_institution_satellite = CreditInstitutionStaticSatelliteFactory()
        cls.account_satellite.hub_entity.link_account_credit_institution.add(
            cls.credit_institution_satellite.hub_entity
        )
        # Create a file to upload
        txt_file_content = b"Test file content"
        cls.txt_file = SimpleUploadedFile("test_file.txt", txt_file_content)
        cls.file_registry_sat_factory = FileUploadRegistryStaticSatelliteFactory(
            file_name=cls.txt_file.name
        )
        cls.file_file_sat_factory = FileUploadFileStaticSatelliteFactory()
        cls.file_registry_sat_factory.hub_entity.link_file_upload_registry_file_upload_file.add(
            cls.file_file_sat_factory.hub_entity
        )

    def test_upload_transaction_to_account_file_view_get(self):
        account_id = self.account_satellite.hub_entity.id
        response = self.client.get(
            f"/file_upload/upload_transaction_to_account_file/{account_id}/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "upload_transaction_to_account_form.html")

    def test_upload_transaction_to_account_file_view_post(self):
        account_id = self.account_satellite.hub_entity.id

        # Create a POST request with the file
        url = reverse("upload_transaction_to_account_file", args=(account_id,))
        data = {"file": self.txt_file}
        request_factory = RequestFactory()
        request = request_factory.post(url, data, format="multipart")
        request.FILES["file"] = self.txt_file

        # Execute the view function
        response = upload_transaction_to_account_file(request, account_id)

        # Assertions
        self.assertEqual(response.status_code, 200)  # Check if redirect

class DownloadTransactionToAccountFileViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.account_satellite = AccountStaticSatelliteFactory()
        cls.credit_institution_satellite = CreditInstitutionStaticSatelliteFactory()
        cls.account_satellite.hub_entity.link_account_credit_institution.add(
            cls.credit_institution_satellite.hub_entity
        )
        # Create a file to upload
        txt_file_content = b"Test file content"
        cls.txt_file = SimpleUploadedFile("test_file.txt", txt_file_content)
        cls.file_registry_sat_factory = FileUploadRegistryStaticSatelliteFactory(
            file_name=cls.txt_file.name
        )
        cls.file_file_sat_factory = FileUploadFileStaticSatelliteFactory(
            file=cls.txt_file
        )
        cls.file_registry_sat_factory.hub_entity.link_file_upload_registry_file_upload_file.add(
            cls.file_file_sat_factory.hub_entity
        )

    def test_download_upload_file(self):
        file_registry_hub_id = self.file_registry_sat_factory.hub_entity.id
        url = reverse("download_upload_file", args=(file_registry_hub_id,))
        request_factory = RequestFactory()
        request = request_factory.get(url)

        # Execute the view function
        response = download_upload_file(request, file_registry_hub_id)
        self.assertEqual(response.status_code, 200)  # Check if redirect


