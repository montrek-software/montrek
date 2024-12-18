import pandas as pd
from django_pandas.io import read_frame
import os

from django.test import TestCase
from showcase.managers.initial_db_data_generator import InitialDbDataGenerator
from showcase.repositories.stransaction_repositories import STransactionRepository
from showcase.tests import TEST_DATA_DIR
from testing.decorators import add_logged_in_user
from django.shortcuts import reverse
from testing.test_cases.view_test_cases import (
    MontrekCreateViewTestCase,
    MontrekFileResponseTestCase,
    MontrekUpdateViewTestCase,
    MontrekListViewTestCase,
    MontrekDeleteViewTestCase,
)
from showcase.factories.stransaction_sat_factories import (
    STransactionFURegistryStaticSatelliteFactory,
    STransactionSatelliteFactory,
)
from showcase.views.stransaction_views import (
    STransactionCreateView,
    STransactionDownloadFileView,
    STransactionFURegistryView,
)
from showcase.views.stransaction_views import STransactionUpdateView
from showcase.views.stransaction_views import STransactionListView
from showcase.views.stransaction_views import STransactionDeleteView


class TestSTransactionCreateView(MontrekCreateViewTestCase):
    viewname = "stransaction_create"
    view_class = STransactionCreateView

    def creation_data(self):
        return {
            "transaction_date": "2021-01-01",
            "transaction_external_identifier": "test_external_identifier",
            "transaction_description": "test_description",
            "transaction_quantity": 100.0,
            "transaction_price": 1.0,
        }


class TestSTransactionUpdateView(MontrekUpdateViewTestCase):
    viewname = "stransaction_update"
    view_class = STransactionUpdateView

    def build_factories(self):
        self.sat_obj = STransactionSatelliteFactory(
            transaction_external_identifier="test"
        )

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}

    def update_data(self):
        return {"transaction_external_identifier": "test_updated"}


class TestSTransactionListView(MontrekListViewTestCase):
    viewname = "stransaction_list"
    view_class = STransactionListView
    expected_no_of_rows = 1

    def build_factories(self):
        self.sat_obj = STransactionSatelliteFactory()


class TestSTransactionDeleteView(MontrekDeleteViewTestCase):
    viewname = "stransaction_delete"
    view_class = STransactionDeleteView

    def build_factories(self):
        self.sat_obj = STransactionSatelliteFactory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}


# TODO: Add tests for FU registry views
class TestSTransactionFURegistryView(MontrekListViewTestCase):
    viewname = "stransaction_fu_registry_list"
    view_class = STransactionFURegistryView
    expected_no_of_rows = 2

    def build_factories(self):
        STransactionFURegistryStaticSatelliteFactory.create_batch(2)


class TestSTransactionDownloadFileView(MontrekFileResponseTestCase):
    viewname = "stransaction_download_file"
    view_class = STransactionDownloadFileView
    is_redirect = True

    def build_factories(self):
        self.sat_obj = STransactionFURegistryStaticSatelliteFactory.create(
            generate_file_upload_file=True
        )

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.hub_entity.get_hub_value_date().pk}

    def test_return_file(self):
        content = b"".join(self.response.streaming_content)
        self.assertEqual(content, b"test")


class TestSTransactionUploadFileView(TestCase):
    @add_logged_in_user
    def setUp(self):
        self.url = reverse("stransaction_upload_file")
        self.test_file_path = os.path.join(
            TEST_DATA_DIR, "stransaction_upload_file.csv"
        )
        self.session_data = {"user_id": self.user.id}
        self.rebase = True

    def test_post__success(self):
        # setup
        InitialDbDataGenerator(self.session_data).generate()
        # run
        with open(self.test_file_path, "rb") as f:
            data = {"file": f}
            response = self.client.post(self.url, data, follow=True)
        # check
        transaction_repo = STransactionRepository(self.session_data)
        actual_db_data = read_frame(transaction_repo.receive())
        check_cols = [
            "transaction_date",
            "transaction_external_identifier",
            "transaction_description",
            "transaction_quantity",
            "transaction_price",
            "product_name",
            "asset_name",
        ]
        actual_db_data = actual_db_data[check_cols]
        expected_db_data_fp = os.path.join(
            TEST_DATA_DIR, "stransaction_expected_db_data.csv"
        )
        if self.rebase:
            actual_db_data.to_csv(expected_db_data_fp, index=False)
        expected_db_data = pd.read_csv(expected_db_data_fp)
        expected_db_data.transaction_date = pd.to_datetime(
            expected_db_data.transaction_date
        ).dt.date
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        message = messages[0]
        self.assertRedirects(response, reverse("stransaction_fu_registry_list"))
        self.assertEqual(str(message), "Successfully processed 993 transactions")
        pd.testing.assert_frame_equal(
            actual_db_data, expected_db_data, check_dtype=False
        )
