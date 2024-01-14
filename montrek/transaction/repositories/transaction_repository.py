from django.utils import timezone
from baseclasses.repositories.montrek_repository import MontrekRepository
from transaction.models import TransactionSatellite
from transaction.models import TransactionHub
from transaction.models import TransactionCategorySatellite
from transaction.models import LinkTransactionTransactionCategory
from account.models import AccountStaticSatellite
from account.models import LinkAccountTransaction


class TransactionRepository(MontrekRepository):
    hub_class = TransactionHub

    def std_queryset(self, **kwargs):
        reference_date = timezone.now()
        self.add_satellite_fields_annotations(
            TransactionSatellite,
            [
                "transaction_amount",
                "transaction_price",
                "transaction_date",
                "transaction_party",
                "transaction_party_iban",
                "transaction_description",
            ],
            reference_date,
        )
        self.add_linked_satellites_field_annotations(
            TransactionCategorySatellite,
            LinkTransactionTransactionCategory,
            ["typename"],
            reference_date,
        )
        self.rename_field("typename", "transaction_category" )

        self.annotations["transaction_value"] = (
            self.annotations["transaction_amount"]
            * self.annotations["transaction_price"]
        )

        return self.build_queryset()

    def get_queryset_with_account(self, **kwargs):
        self.add_linked_satellites_field_annotations(
            AccountStaticSatellite,
            LinkAccountTransaction,
            ["account_name", "hub_entity_id"],
            self.reference_date,
            reversed_link=True,
        )
        self.rename_field("hub_entity_id", "account_id" )
        return self.std_queryset(**kwargs)
