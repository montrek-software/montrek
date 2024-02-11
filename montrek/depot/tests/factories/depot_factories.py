import factory
from account.models import AccountStaticSatellite
from currency.tests.factories.currency_factories import (
    CurrencyTimeSeriesSatelliteFactory,
)
from transaction.tests.factories.transaction_factories import (
    TransactionSatelliteFactory,
)
from asset.tests.factories.asset_factories import (
    AssetStaticSatelliteFactory,
    AssetTimeSeriesSatelliteFactory,
)
from account.tests.factories.account_factories import AccountStaticSatelliteFactory


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
                transaction_date="2020-12-31",
            )
            assets = AssetTimeSeriesSatelliteFactory.create_batch(
                3, price=1.2, value_date="2021-01-01"
            )
            currency = CurrencyTimeSeriesSatelliteFactory.create(
                fx_rate=1, value_date="2021-01-01"
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
                    transaction_date="2021-01-01",
                )
                TransactionSatelliteFactory.create(
                    hub_entity__account=self.hub_entity,
                    transaction_amount=1,
                    transaction_price=-2,
                    transaction_date="2021-01-01",
                )
