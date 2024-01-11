from django.utils import timezone
from baseclasses.repositories.montrek_repository import MontrekRepository
from baseclasses.repositories.db_creator import DbCreator
from transaction.models import TransactionCategoryMapHub
from transaction.models import TransactionCategoryMapSatellite
from transaction.models import TransactionCategoryHub
from transaction.models import TransactionCategorySatellite
from transaction.models import TransactionHub
from transaction.models import TransactionSatellite
from transaction.models import LinkTransactionTransactionCategory
from transaction.models import LinkTransactionCategoryMapCounterTransactionAccount
from transaction.repositories.transaction_repository import TransactionRepository
from account.models import AccountStaticSatellite
from account.models import BankAccountStaticSatellite
from account.models import LinkAccountTransactionCategoryMap


class TransactionCategoryMapRepository(MontrekRepository):
    hub_class = TransactionCategoryMapHub

    def std_queryset(self):
        reference_date = timezone.now()
        self.add_satellite_fields_annotations(
            TransactionCategoryMapSatellite,
            [
                "field",
                "value",
                "category",
                "is_regex",
            ],
            reference_date,
        )
        self.add_linked_satellites_field_annotations(
            AccountStaticSatellite,
            LinkAccountTransactionCategoryMap,
            ["account_name", "hub_entity_id"],
            self.reference_date,
            reversed_link=True,
        )
        self.rename_field("hub_entity_id", "account_id")
        self.add_linked_satellites_field_annotations(
            BankAccountStaticSatellite,
            LinkAccountTransactionCategoryMap,
            ["bank_account_iban"],
            self.reference_date,
            reversed_link=True,
        )
        self.add_linked_satellites_field_annotations(
            AccountStaticSatellite,
            LinkTransactionCategoryMapCounterTransactionAccount,
            ["hub_entity_id"],
            self.reference_date,
        )
        self.rename_field("hub_entity_id", "counter_transaction_account_id")
        return self.build_queryset()


class TransactionCategoryRepository(MontrekRepository):
    hub_class = TransactionCategoryHub

    def std_queryset(self):
        reference_date = timezone.now()
        self.add_satellite_fields_annotations(
            TransactionCategorySatellite,
            [
                "typename",
            ],
            reference_date,
        )
        return self.build_queryset().order_by("typename")
