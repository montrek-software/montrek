import factory
from transaction.tests.factories.transaction_factories import (
    TransactionSatelliteFactory,
)
from asset.tests.factories.asset_factories import AssetHubFactory
from account.tests.factories.account_factories import AccountStaticSatelliteFactory


class DepotAccountFactory(AccountStaticSatelliteFactory):
    @factory.post_generation
    def depot_data(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            # No mechanism to create depot data installed yet
            return
        else:
            # Create three assets and tree transactions for each asset
            assets = AssetHubFactory.create_batch(3)
            for asset in assets:
                TransactionSatelliteFactory.create(
                    hub_entity__asset=asset,
                    hub_entity__account=self.hub_entity,
                    transaction_amount=1,
                    transaction_price=1,
                    transaction_date="2021-01-01",
                )
