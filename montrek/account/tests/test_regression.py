import os
from django.test import TestCase
from account.tests.factories.account_factories import BankAccountStaticSatelliteFactory
from account.tests.factories.account_factories import AccountStaticSatelliteFactory
from account.managers.transaction_upload_methods import upload_dkb_transactions
from credit_institution.tests.factories.credit_institution_factories import (
    CreditInstitutionStaticSatelliteFactory,
)
from baseclasses.repositories.db_creator import DbCreator
from transaction.models import TransactionHub, TransactionSatellite
from transaction.repositories.transaction_repository import TransactionRepository
from transaction.tests.factories.transaction_factories import (
    TransactionCategorySatelliteFactory,
)


class AccountRegressionTests(TestCase):
    test_csv_path = os.path.join(
        os.path.dirname(__file__), "managers/data/dkb_test.csv"
    )

    @classmethod
    def setUpTestData(cls):
        cls.bank_account = BankAccountStaticSatelliteFactory.create()
        AccountStaticSatelliteFactory.create(
            hub_entity=cls.bank_account.hub_entity,
            account_type="BankAccount",
        )
        cls.credit_institution = CreditInstitutionStaticSatelliteFactory.create(
            account_upload_method="dkb"
        )
        cls.bank_account.hub_entity.link_account_credit_institution.add(
            cls.credit_institution.hub_entity
        )

    def test_upload_dkb_transactions_and_change_transaction_category(self):
        transactions = upload_dkb_transactions(
            self.bank_account.hub_entity, self.test_csv_path
        )
        self.assertEqual(len(transactions), 15)

        repository = TransactionRepository({})
        query = repository.std_queryset()
        test_data = repository.object_to_dict(query.first())

        test_category = TransactionCategorySatelliteFactory.create(typename="TestCat")
        test_data["link_transaction_transaction_category"] = test_category.hub_entity
        creator = DbCreator(
            hub_entity_class=TransactionHub, satellite_classes=[TransactionSatellite]
        )
        creator.create(test_data, TransactionHub())
        creator.save_stalled_objects()
        self.assertEqual(len(transactions), 15)
        self.assertEqual(query.first().typename, "TestCat")

    def test_upload_dkb_transaction_with_empty_auftraggeber(self):
        empty_csv_path = os.path.join(
            os.path.dirname(__file__), "managers/data/dkb_empty_auftraggeber.csv"
        )
        transactions = upload_dkb_transactions(
            self.bank_account.hub_entity, empty_csv_path
        )
        self.assertEqual(len(transactions), 2)
