import os
from django.test import TestCase
from django.utils import timezone
from account.managers.onvista_file_upload_manager import (
    OnvistaFileUploadDepotProcessor,
    OnvistaFileUploadTransactionProcessor,
    OnvistaFileUploadProcessor,
)
from account.managers.not_implemented_processor import NotImplementedFileUploadProcessor
from account.tests.factories.account_factories import (
    AccountStaticSatelliteFactory,
)
from account.repositories.account_repository import AccountRepository
from asset.repositories.asset_repository import AssetRepository
from transaction.tests.factories.transaction_factories import (
    TransactionSatelliteFactory,
    TransactionHubFactory,
)


class TestOnvistaFileUploadManager(TestCase):
    def setUp(self):
        account_sat = AccountStaticSatelliteFactory.create(account_name="Test Account")
        self.account = (
            AccountRepository().std_queryset().get(pk=account_sat.hub_entity.pk)
        )

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
        self.assertEqual(processor.message, "Not implemented")
        self.assertIsInstance(processor.subprocessor, NotImplementedFileUploadProcessor)

    def test_empty_file(self):
        processor = OnvistaFileUploadProcessor(self.account)
        test_path = "/tmp/test_file.csv"
        with open(test_path, "w"):
            ...
        result = processor.pre_check(test_path)
        self.assertEqual(result, False)
        self.assertEqual(processor.message, "Not implemented")
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
        # Compare created assets to input data
        self.assertEqual(assets.count(), 3)
        for _, row in processor.subprocessor.input_data_df.iterrows():
            asset = assets.get(asset_isin=row.asset_isin)
            self.assertEqual(asset.asset_name, row.asset_name)
            self.assertEqual(float(asset.price), round(row.price, 4))
            self.assertEqual(asset.value_date, row.value_date.date())
            self.assertEqual(asset.asset_type, row.asset_type)
            self.assertEqual(asset.asset_wkn, row.asset_wkn)
            self.assertEqual(asset.asset_isin, row.asset_isin)
        # post_check does not agree with the number of shares the account holds
        result = processor.post_check(test_path)
        self.assertFalse(result)
        self.assertTrue(
            processor.subprocessor.message.startswith(
                "Mismatch between input data and depot data"
            )
        )
        # add transactions in accordance to input data
        for _, row in processor.subprocessor.input_data_df.iterrows():
            asset = assets.get(asset_name=row["asset_name"])
            transaction_hub = TransactionHubFactory.create(
                account=self.account, asset=asset
            )
            transaction_date = timezone.make_aware(
                timezone.datetime.strptime(str(row["value_date"])[:10], "%Y-%m-%d")
            )
            TransactionSatelliteFactory.create(
                hub_entity=transaction_hub,
                transaction_amount=row["quantity"],
                transaction_price=row["price"],
                transaction_date=transaction_date,
            )
        result = processor.post_check(test_path)
        self.assertTrue(result)

    def test_transaction_processor(self):
        processor = OnvistaFileUploadProcessor(self.account)
        test_path = os.path.join(
            os.path.dirname(__file__), "data", "onvista_transaction_test.csv"
        )
        result = processor.pre_check(test_path)
        self.assertEqual(result, True)
        self.assertIsInstance(
            processor.subprocessor, OnvistaFileUploadTransactionProcessor
        )
        self.assertEqual(
            processor.subprocessor.input_data_dfs["asset_purchase"].shape, (5, 5)
        )
        result = processor.process(test_path)
        self.assertEqual(result, True)
        transactions = AccountRepository().get_transaction_table_by_account(
            self.account.pk
        )
        self.assertEqual(transactions.count(), 6)
        assets = AccountRepository().get_depot_data(self.account.pk)
        self.assertEqual(assets.count(), 3)
