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
)
from credit_institution.models import CreditInstitutionStaticSatellite
from transaction.models import TransactionSatellite


from baseclasses.repositories.montrek_repository import MontrekRepository
from depot.managers.depot_stats import DepotStats
from transaction.repositories.transaction_account_queries import (
    get_transactions_by_account_hub,
)
from transaction.repositories.transaction_repository import TransactionRepository


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
            "link_account_credit_institution",
            ["credit_institution_name", "credit_institution_bic"],
            reference_date,
        )
        self.annotations.update({"account_value": self._account_value()})
        queryset = self.build_queryset()
        return queryset

    def transaction_table_queryset(self, **kwargs):
        return (
            TransactionRepository()
            .std_queryset()
            .filter(link_transaction_account=OuterRef("pk"))
        )

    def _account_value(self):
        return Case(
            When(
                account_type=AccountStaticSatellite.AccountType.DEPOT,
                then=Value(100, output_field=FloatField()),
            ),
            default=self._get_bank_account_value(),
        )

    def _get_bank_account_value(self):
        transaction_amount_sq = Subquery(
            self.transaction_table_queryset()
            .values("link_transaction_account")
            .annotate(
                account_value=Sum(F("transaction_amount") * F("transaction_price"))
            )
            .values("account_value")
        )

        return Sum(transaction_amount_sq, output_field=FloatField())

    def _get_depot_account_value(self):
        return DepotStats(self._hub_entity_id, timezone.now()).current_value
