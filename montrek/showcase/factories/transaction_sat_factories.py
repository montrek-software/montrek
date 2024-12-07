import random
from dataclasses import dataclass
import factory
from enum import Enum


from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekTSSatelliteFactory,
)
from showcase.factories.transaction_hub_factories import (
    TransactionHubValueDateFactory,
)
from showcase.models.transaction_sat_models import TransactionSatellite


@dataclass
class TransactionConfig:
    description: str
    min_quantity: float
    max_quantity: float
    min_price: float
    max_price: float


class TransactionChoices(Enum):
    SECURITY_PURCHASE = TransactionConfig(
        "security purchase", 0, 100_000_000, 0.01, 10_000
    )
    SECURITY_SALE = TransactionConfig("security sale", -100_000_000, 0, 0.01, 10_000)
    DIVIDEND_PAYMENT = TransactionConfig("dividend payment", 0, 1_000_000, 0.01, 100)
    FEE_PAYMENT = TransactionConfig("fee payment", -1_000_000, 0, 0.01, 1_000)


class TransactionSatelliteFactory(MontrekTSSatelliteFactory):
    class Meta:
        model = TransactionSatellite
        exclude = ["config"]

    hub_value_date = factory.SubFactory(TransactionHubValueDateFactory)
    transaction_external_identifier = factory.Faker("ssn")

    @factory.lazy_attribute
    def config(self):
        return random.choice(list(TransactionChoices)).value

    @factory.lazy_attribute
    def transaction_description(self):
        return self.config.description

    @factory.lazy_attribute
    def transaction_quantity(self):
        return random.uniform(self.config.min_quantity, self.config.max_quantity)

    @factory.lazy_attribute
    def transaction_price(self):
        return random.uniform(self.config.min_price, self.config.max_price)
