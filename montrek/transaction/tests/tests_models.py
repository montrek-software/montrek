import hashlib
from django.utils import timezone
from django.test import TestCase
from transaction.models import TransactionSatellite
from transaction.tests.factories.transaction_factories import TransactionHubFactory

class TestAccountIdentifier(TestCase):
    def test_account_identifier(self):
        transaction_date = timezone.datetime(2023,1,1,13,3,0)
        transaction_type = 'testtype'
        transaction_party = 'testparty'
        transaction_category = 'testcategory'
        account_sat = TransactionSatellite.objects.create(
            hub_entity=TransactionHubFactory(),
            transaction_date=transaction_date,
            transaction_type=transaction_type,
            transaction_party=transaction_party,
            transaction_category=transaction_category,
            transaction_amount=100,
            transaction_description='bliblubb',
            transaction_price=1.2,
        )
        id_str = ''.join([str(field) for field in [
            transaction_date,
            transaction_type,
            transaction_party,
            transaction_category,
        ]])
        test_hash = hashlib.sha256(id_str.encode()).hexdigest()
        self.assertEqual(account_sat.hash_identifier, test_hash)

    def test_account_identifier_not_equal(self):
        transaction_date = timezone.datetime(2023,1,1,13,3,0)
        transaction_type = 'testtype'
        transaction_party = 'testparty'
        transaction_category = 'testcategory'
        account_sat = TransactionSatellite.objects.create(
            hub_entity=TransactionHubFactory(),
            transaction_date=timezone.datetime(2023,1,1,13,4,0),
            transaction_type=transaction_type,
            transaction_party=transaction_party,
            transaction_category=transaction_category,
            transaction_amount=100,
            transaction_description='bliblubb',
            transaction_price=1.2,
        )
        id_str = ''.join([str(field) for field in [
            transaction_date,
            transaction_type,
            transaction_party,
            transaction_category,
        ]])
        test_hash = hashlib.sha256(id_str.encode()).hexdigest()
        self.assertNotEqual(account_sat.hash_identifier, test_hash)

