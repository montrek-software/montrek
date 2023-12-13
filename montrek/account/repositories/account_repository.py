from django.utils import timezone
from django.db.models import (
    Sum,
    F,
    Prefetch,
    FloatField,
    Case,
    When,
    Value,
    Subquery,
    OuterRef,
)
from account.models import (
    AccountHub,
    AccountStaticSatellite,
    BankAccountPropertySatellite,
    BankAccountStaticSatellite,
    LinkAccountCreditInstitution,
)
from credit_institution.models import CreditInstitutionStaticSatellite
from transaction.models import TransactionSatellite


from baseclasses.repositories.montrek_repository import MontrekRepository
from baseclasses.repositories.montrek_repository import paginated_table
from depot.repositories.depot_repository import DepotRepository
from transaction.repositories.transaction_account_queries import (
    get_transactions_by_account_hub,
)
from transaction.repositories.transaction_repository import TransactionRepository
from transaction.repositories.transaction_category_repository import TransactionCategoryMapRepository
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepository,
)


class AccountRepository(MontrekRepository):
    hub_class = AccountHub

    def std_queryset(self, **kwargs):
        reference_date = timezone.now()
        self.add_satellite_fields_annotations(
            AccountStaticSatellite, ["account_name", "account_type"], reference_date
        )
        self.add_satellite_fields_annotations(
            BankAccountStaticSatellite, ["bank_account_iban"], reference_date
        )
        self.add_linked_satellites_field_annotations(
            CreditInstitutionStaticSatellite,
            LinkAccountCreditInstitution,
            ["credit_institution_name", "credit_institution_bic"],
            reference_date,
        )
        self._account_value()
        queryset = self.build_queryset()
        return queryset

    @paginated_table
    def get_transaction_table_by_account_paginated(self, account_hub_id):
        return self.get_transaction_table_by_account(account_hub_id)

    def get_transaction_table_by_account(self, account_hub_id):
        hub_entity = self.hub_class.objects.get(pk=account_hub_id)
        transactions = (
            TransactionRepository(self.request)
            .std_queryset()
            .filter(
                link_transaction_account=hub_entity,
                transaction_date__lte=self.session_end_date,
                transaction_date__gte=self.session_start_date,
            )
            .order_by("-transaction_date")

        )
        return transactions

    def transaction_table_subquery(self, **kwargs):
        return (
            TransactionRepository(self.request)
            .std_queryset()
            .filter(
                link_transaction_account=OuterRef("pk"),
                transaction_date__lte=self.session_end_date,
            )
        )

    def _account_value(self):
        return Case(
            When(
                account_type=AccountStaticSatellite.AccountType.DEPOT,
                then=self._get_depot_account_value(),
            ),
            default=self._get_bank_account_value(),
        )

    def _get_bank_account_value(self):
        transaction_amount_sq = Subquery(
            self.transaction_table_subquery()
            .values("link_transaction_account")
            .annotate(account_value=Sum(F("transaction_value")))
            .values("account_value")
        )
        self.annotations["account_value"] = transaction_amount_sq

    def _get_depot_account_value(self):
        #TODO: Set to Depot Value
        return self._get_bank_account_value()

    @paginated_table
    def get_upload_registry_table_by_account_paginated(self, account_hub_id: int):
        hub_entity = self.hub_class.objects.get(pk=account_hub_id)
        return FileUploadRegistryRepository(self.request).std_queryset().filter(
            link_file_upload_registry_account=hub_entity
        ).order_by('-created_at')

    @paginated_table
    def get_transaction_category_map_table_by_account_paginated(self, account_hub_id:int):
        hub_entity = self.hub_class.objects.get(pk=account_hub_id)
        return TransactionCategoryMapRepository(self.request).std_queryset().filter(
            link_transaction_category_map_account=hub_entity
        ).order_by('-created_at')

    @paginated_table
    def get_depot_stats_table_by_account_paginated(self, account_hub_id: int):
        hub_entity = self.hub_class.objects.get(pk=account_hub_id)
        return (
            DepotRepository(self.request)
            .std_queryset()
            .filter(account_id=hub_entity.id)
        )
