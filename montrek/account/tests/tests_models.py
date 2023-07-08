import hashlib
from django.test import TestCase
from account.models import AccountStaticSatellite
from account.models import BankAccountStaticSatellite
from account.models import BankAccountPropertySatellite
from account.tests.factories.account_factories import AccountHubFactory

class TestAccountIdentifier(TestCase):
    def test_account_identifier(self):
        account_type = 'Other'
        account_name = 'Test Account'
        account_sat = AccountStaticSatellite.objects.create(
            account_type=account_type, 
            account_name=account_name,
            hub_entity=AccountHubFactory(),
        )
        test_hash = hashlib.sha256((account_type + account_name).encode()).hexdigest()
        self.assertEqual(account_sat.hash_identifier, test_hash)

    def test_account_identifier_not_equal(self):
        account_type = 'Other'
        account_name = 'Test Account2'
        account_sat = AccountStaticSatellite.objects.create(
            account_type=account_type, 
            account_name='Test Account',
            hub_entity=AccountHubFactory(),
        )
        test_hash = hashlib.sha256((account_type + account_name).encode()).hexdigest()
        self.assertNotEqual(account_sat.hash_identifier, test_hash)

    def test_bank_account_identifier(self):
        iban = 'DE00000000000000000000'
        account_sat = BankAccountStaticSatellite.objects.create(
            bank_account_iban=iban,
            hub_entity=AccountHubFactory(),
        )
        test_hash = hashlib.sha256(iban.encode()).hexdigest()
        self.assertEqual(account_sat.hash_identifier, test_hash)

    def test_bank_account_identifier(self):
        iban = 'DE00000000000000000000'
        account_sat = BankAccountStaticSatellite.objects.create(
            bank_account_iban='DE00000000000000000001',
            hub_entity=AccountHubFactory(),
        )
        test_hash = hashlib.sha256(iban.encode()).hexdigest()
        self.assertNotEqual(account_sat.hash_identifier, test_hash)

    def test_bank_account_property_identifier(self):
        account_sat = BankAccountPropertySatellite.objects.create(
            hub_entity = AccountHubFactory(),
        )
        test_hash = hashlib.sha256(str(account_sat.hub_entity_id).encode()).hexdigest()
        self.assertEqual(account_sat.hash_identifier, test_hash)
