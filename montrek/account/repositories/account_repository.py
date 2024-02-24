from decimal import Decimal
from django.db.models.fields import decimal
from django.utils import timezone
from django.db.models import (
    DecimalField,
    ExpressionWrapper,
    QuerySet,
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
from numpy import who
from account.models import (
    AccountHub,
    AccountStaticSatellite,
    BankAccountPropertySatellite,
    BankAccountStaticSatellite,
    LinkAccountCreditInstitution,
)
from credit_institution.models import CreditInstitutionStaticSatellite


from baseclasses.repositories.montrek_repository import MontrekRepository
from baseclasses.repositories.montrek_repository import paginated_table
from depot.repositories.depot_repository import DepotRepository
from mt_accounting.transaction.repositories.transaction_repository import (
    TransactionRepository,
)
from mt_accounting.transaction.repositories.transaction_category_repository import (
    TransactionCategoryMapRepository,
)
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepository,
)


class AccountRepository(MontrekRepository):
    hub_class = AccountHub

    def std_queryset(self, **kwargs) -> QuerySet:
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
            [
                "credit_institution_name",
                "credit_institution_bic",
                "account_upload_method",
            ],
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
        transaction_repository = TransactionRepository(self.session_data)
        transactions = (
            transaction_repository.std_queryset()
            .filter(
                link_transaction_account=hub_entity,
                transaction_date__lte=self.session_end_date,
                transaction_date__gte=self.session_start_date,
            )
            .order_by("-transaction_date")
        )
        self.messages += transaction_repository.messages
        if "sort_field" in self.session_data:
            transactions = transactions.order_by(self.session_data["sort_field"][0])
        return transactions

    def transaction_table_subquery(self, **kwargs):
        return (
            TransactionRepository(self.session_data)
            .std_queryset()
            .filter(
                link_transaction_account=OuterRef("pk"),
                transaction_date__lte=self.session_end_date,
            )
        )

    def _account_value(self):
        self.annotations["account_cash"] = self._get_bank_account_cash()
        self.annotations["account_depot_value"] = Case(
            When(
                account_type=AccountStaticSatellite.AccountType.DEPOT,
                then=self._get_depot_value(),
            ),
            default=Value(Decimal(0.0)),
        )
        self.annotations["account_depot_book_value"] = Case(
            When(
                account_type=AccountStaticSatellite.AccountType.DEPOT,
                then=self._get_depot_book_value(),
            ),
            default=Value(Decimal(0.0)),
        )
        self.annotations["account_depot_pnl"] = Case(
            When(
                account_type=AccountStaticSatellite.AccountType.DEPOT,
                then=self._get_depot_pnl(),
            ),
            default=Value(Decimal(0.0)),
        )
        self.annotations["account_depot_performance"] = Case(
            When(
                account_type=AccountStaticSatellite.AccountType.DEPOT,
                then=self._get_depot_performance(),
            ),
            default=Value(Decimal(0.0)),
        )
        self.annotations["account_value"] = Case(
            When(
                account_type=AccountStaticSatellite.AccountType.BANK_ACCOUNT,
                then=F("account_cash"),
            ),
            When(
                account_type=AccountStaticSatellite.AccountType.DEPOT,
                then=self._get_depot_account_value(),
            ),
            When(
                account_type=AccountStaticSatellite.AccountType.OTHER,
                then=Value(Decimal(0.0)),
            ),
        )

    def _get_bank_account_cash(self):
        transaction_amount_sq = Subquery(
            self.transaction_table_subquery()
            .values("link_transaction_account")
            .annotate(account_value=Sum(F("transaction_value")))
            .values("account_value")
        )
        return transaction_amount_sq

    def _get_depot_value(self):
        return self._get_depot_subquery("value")

    def _get_depot_book_value(self):
        return self._get_depot_subquery("book_value")

    def _get_depot_pnl(self):
        return ExpressionWrapper(
            F("account_depot_value") - F("account_depot_book_value"),
            output_field=DecimalField(),
        )

    def _get_depot_performance(self):
        return ExpressionWrapper(
            F("account_depot_pnl") / F("account_depot_book_value"),
            output_field=DecimalField(),
        )

    def _get_depot_account_value(self):
        return ExpressionWrapper(
            F("account_cash") + F("account_depot_value"), output_field=DecimalField()
        )

    def _get_depot_subquery(self, field):
        return Subquery(
            self.get_depot_data(OuterRef("pk"))
            .values("account_id")
            .annotate(**{field: Sum(F(field))})
            .values(field)
        )

    @paginated_table
    def get_upload_registry_table_by_account_paginated(self, account_hub_id: int):
        hub_entity = self.hub_class.objects.get(pk=account_hub_id)
        return (
            FileUploadRegistryRepository(self.session_data)
            .std_queryset()
            .filter(link_file_upload_registry_account=hub_entity)
            .order_by("-created_at")
        )

    @paginated_table
    def get_transaction_category_map_table_by_account_paginated(
        self, account_hub_id: int
    ):
        hub_entity = self.hub_class.objects.get(pk=account_hub_id)
        return (
            TransactionCategoryMapRepository(self.session_data)
            .std_queryset()
            .filter(link_transaction_category_map_account=hub_entity)
            .order_by("-created_at")
        )

    def get_depot_data(self, account_hub_id: int):
        return (
            DepotRepository(self.session_data)
            .std_queryset()
            .filter(account_id=account_hub_id)
        )

    @paginated_table
    def get_depot_stats_table_by_account_paginated(self, account_hub_id: int):
        return self.get_depot_data(account_hub_id)
