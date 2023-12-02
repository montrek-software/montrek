from django.utils import timezone
from django.db.models import Sum, F, Prefetch
from account.models import (
    AccountHub,
    AccountStaticSatellite,
    BankAccountPropertySatellite,
    BankAccountStaticSatellite,
)
from credit_institution.models import CreditInstitutionStaticSatellite


from baseclasses.repositories.db_helper import get_satellite_from_hub_query
from baseclasses.repositories.db_helper import select_satellite
from baseclasses.repositories.montrek_repository import MontrekRepository
from depot.managers.depot_stats import DepotStats
from transaction.repositories.transaction_account_queries import (
    get_transactions_by_account_hub,
)


class AccountRepository(MontrekRepository):
    def __init__(self):
        super().__init__(AccountHub)

    def detail_queryset(self, **kwargs):
        reference_date = timezone.now()
        account_static_fields = self.add_satellite_fields_annotations(
            AccountStaticSatellite, ["account_name", "account_type"], reference_date
        )
        bank_account_static_fields = self.add_satellite_fields_annotations(
            BankAccountStaticSatellite, ["bank_account_iban"], reference_date
        )
        #account_value = Sum(self._account_value())
        credit_institution_fields = self.add_linked_satellites_field_annotations(
            CreditInstitutionStaticSatellite,
            "link_account_credit_institution",
            ["credit_institution_name", "credit_institution_bic"],
            reference_date,
        )
        queryset = self.build_queryset()
        return queryset

    def table_queryset(self, **kwargs):
        return AccountStaticSatellite.objects.all()

    def _account_value(self):
        account_statics = self._static_satellite
        if (
            account_statics.account_type
            == AccountStaticSatellite.AccountType.BANK_ACCOUNT
        ):
            return self._get_bank_account_value()
        if account_statics.account_type == AccountStaticSatellite.AccountType.DEPOT:
            return self._get_depot_account_value()
        raise NotImplementedError(
            f"Account type {account_statics.account_type} not implemented"
        )

    def _get_bank_account_value(self):
        transactions = get_transactions_by_account_hub(self._hub_entity)
        return (
            transactions.aggregate(
                total_value=Sum(F("transaction_amount") * F("transaction_price"))
            )["total_value"]
            or 0
        )

    def _get_depot_account_value(self):
        return DepotStats(self._hub_entity_id, timezone.now()).current_value
