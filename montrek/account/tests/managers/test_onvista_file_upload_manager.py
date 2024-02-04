import os
from django.test import TestCase
from account.managers.onvista_file_upload_manager import (
    OnvistaFileUploadDepotProcessor,
    OnvistaFileUploadProcessor,
)
from account.managers.not_implemented_processor import NotImplementedFileUploadProcessor
from account.tests.factories.account_factories import AccountHubFactory
from account.repositories.account_repository import AccountRepository
from asset.repositories.asset_repository import AssetRepository
from currency.tests.factories.currency_factories import CurrencyStaticSatelliteFactory


class TestOnvistaFileUploadManager(TestCase):
    def setUp(self):
        account_hub = AccountHubFactory()
        self.account = AccountRepository().std_queryset().get(pk=account_hub.pk)

    def test_default_processor(self):
        processor = OnvistaFileUploadProcessor(self.account)
        self.assertEqual(processor.message, "Not implemented")

    def test_no_type_detectable(self):
        processor = OnvistaFileUploadProcessor(self.account)
        test_path = "/tmp/test_file.csv"
        with open(test_path, "w") as f:
            f.write("UNKNOWN")
        result = processor.pre_check(test_path)
        self.assertEqual(result, False)
        self.assertEqual(processor.message, "File cannot be processed")
        self.assertIsInstance(processor.subprocessor, NotImplementedFileUploadProcessor)

    def test_empty_file(self):
        processor = OnvistaFileUploadProcessor(self.account)
        test_path = "/tmp/test_file.csv"
        with open(test_path, "w"):
            ...
        result = processor.pre_check(test_path)
        self.assertEqual(result, False)
        self.assertEqual(processor.message, "File cannot be processed")
        self.assertIsInstance(processor.subprocessor, NotImplementedFileUploadProcessor)

    def test_depotuebersicht_processor(self):
        processor = OnvistaFileUploadProcessor(self.account)
        test_path = os.path.join(os.path.dirname(__file__), "data", "onvista_test.csv")
        result = processor.pre_check(test_path)
        self.assertEqual(result, True)
        self.assertIsInstance(processor.subprocessor, OnvistaFileUploadDepotProcessor)
        result = processor.process(test_path)
        self.assertEqual(result, True)
        self.assertEqual(processor.subprocessor.input_data_df.shape, (3, 24))
        assets = AssetRepository().std_queryset()
        self.assertEqual(assets.count(), 3)
        for _, row in processor.subprocessor.input_data_df.iterrows():
            asset = assets.get(asset_isin=row.asset_isin)
            self.assertEqual(asset.asset_name, row.asset_name)
            self.assertEqual(float(asset.price), round(row.price, 4))
            self.assertEqual(asset.value_date, row.value_date.date())
            self.assertEqual(asset.asset_type, row.asset_type)
            self.assertEqual(asset.asset_wkn, row.asset_wkn)
            self.assertEqual(asset.asset_isin, row.asset_isin)
