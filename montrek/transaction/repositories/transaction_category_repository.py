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
from transaction.repositories.transaction_repository import TransactionRepository
from account.models import AccountStaticSatellite
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
        return self.build_queryset()

    def std_create_object(self, data):
        super().std_create_object(data)
        account_hub = data["link_transaction_category_map_account"]
        category = data["category"]
        transaction_category_repository = TransactionCategoryRepository()
        transaction_category_repository.std_create_object(
            {
                "typename": category,
            }
        )
        transaction_category = transaction_category_repository.std_queryset().get(
            typename=category,
            state_date_start__lte=self.reference_date,
            state_date_end__gte=self.reference_date,
        )
        transaction_repository = TransactionRepository()
        transactions = transaction_repository.get_queryset_with_account().filter(
            account_id=account_hub.id,
            **{data["field"]: data["value"]},
        )
        creation_date = timezone.now()
        for transaction in transactions:
            db_creator = DbCreator(transaction, [TransactionSatellite])
            link = db_creator.create_new_link(
                LinkTransactionTransactionCategory,
                transaction,
                transaction_category,
                creation_date,
            )
            link.save()


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
