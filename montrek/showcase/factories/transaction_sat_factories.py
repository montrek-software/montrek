import factory

from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekTSSatelliteFactory,
)
from showcase.factories.transaction_hub_factories import (
    TransactionHubValueDateFactory,
)
from showcase.models.transaction_sat_models import TransactionSatellite


class TransactionSatelliteFactory(MontrekTSSatelliteFactory):
    class Meta:
        model = TransactionSatellite

    hub_value_date = factory.SubFactory(TransactionHubValueDateFactory)
    transaction_external_identifier = factory.Faker("ssn")
    transaction_description = factory.Faker(
        "random_element",
        elements=["security purchase", "security sale", "dividend payment"],
    )
    transaction_quantity = factory.Faker("pyfloat")
    transaction_price = factory.Faker("pyfloat")
