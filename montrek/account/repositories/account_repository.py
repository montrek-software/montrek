from django.utils import timezone
from account.models import (
    AccountHub,
    AccountStaticSatellite,
    BankAccountPropertySatellite,
    BankAccountStaticSatellite,
)


from baseclasses.repositories.db_helper import get_satellite_from_hub_query
from baseclasses.repositories.db_helper import get_satellite_field_subqueries
from baseclasses.repositories.montrek_repository import MontrekRepository


class AccountRepository(MontrekRepository):
    def __init__(self, hub_entity_id):
        self._hub_entity_id = hub_entity_id
        self._hub_entity = AccountHub.objects.get(pk=hub_entity_id)
        self._static_satellite = get_satellite_from_hub_query(
            self._hub_entity, AccountStaticSatellite
        )
        self._property_satellite = get_satellite_from_hub_query(
            self._hub_entity, BankAccountPropertySatellite
        )
        self._bank_account_satellite = get_satellite_from_hub_query(
            self._hub_entity, BankAccountStaticSatellite
        )

    def detail_queryset(self, **kwargs):
        reference_date = timezone.now()
        account_static_fields = get_satellite_field_subqueries(
            AccountStaticSatellite, ["account_name"], reference_date
        )
        bank_account_static_fields = get_satellite_field_subqueries(
            BankAccountStaticSatellite, ["bank_account_iban"], reference_date
        )
        annotations = {**account_static_fields, **bank_account_static_fields}
        return AccountHub.objects.filter(pk=self._hub_entity_id).annotate(**annotations)

    def table_queryset(self, **kwargs):
        return AccountStaticSatellite.objects.all()
