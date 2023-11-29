from account.models import (
    AccountHub,
    AccountStaticSatellite,
    BankAccountPropertySatellite,
    BankAccountStaticSatellite,
)


from baseclasses.repositories.db_helper import get_satellite_from_hub_query
from baseclasses.repositories.montrek_repository import MontrekRepository


class AccountRepository(MontrekRepository):
    def __init__(self, hub_entity_id):
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
        return self._static_satellite

    def table_queryset(self, **kwargs):
        return AccountStaticSatellite.objects.all()
