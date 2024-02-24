import factory
from account.models import AccountStaticSatellite
from currency.tests.factories.currency_factories import (
    CurrencyTimeSeriesSatelliteFactory,
)
from mt_accounting.transaction.tests.factories.transaction_factories import (
    TransactionSatelliteFactory,
)
from asset.tests.factories.asset_factories import (
    AssetStaticSatelliteFactory,
    AssetTimeSeriesSatelliteFactory,
)
from account.tests.factories.account_factories import AccountStaticSatelliteFactory
from baseclasses.utils import montrek_time


class DepotAccountFactory(AccountStaticSatelliteFactory):
    account_type = AccountStaticSatellite.AccountType.DEPOT

    @factory.post_generation
    def depot_data(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            # No mechanism to create depot data installed yet
            return
        else:
            # Get 4 Euros cash
            TransactionSatelliteFactory.create(
                hub_entity__account=self.hub_entity,
                transaction_amount=4,
                transaction_price=1,
                transaction_date=montrek_time(2020, 12, 31),
            )
            assets = AssetTimeSeriesSatelliteFactory.create_batch(
                3, price=1.2, value_date=montrek_time(2021, 1, 1)
            )
            currency = CurrencyTimeSeriesSatelliteFactory.create(
                fx_rate=1, value_date=montrek_time(2021, 1, 1)
            )
            for asset in assets:
                AssetStaticSatelliteFactory.create(
                    hub_entity=asset.hub_entity,
                    currency=currency.hub_entity,
                )
                TransactionSatelliteFactory.create(
                    hub_entity__asset=asset.hub_entity,
                    hub_entity__account=self.hub_entity,
                    transaction_amount=1,
                    transaction_price=1,
                    transaction_date=montrek_time(2021, 1, 1),
                )
                TransactionSatelliteFactory.create(
                    hub_entity__account=self.hub_entity,
                    transaction_amount=1,
                    transaction_price=-2,
                    transaction_date=montrek_time(2021, 1, 1),
                )
