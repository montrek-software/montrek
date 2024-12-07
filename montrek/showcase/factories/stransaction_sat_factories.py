import random
from dataclasses import dataclass
import factory
from enum import Enum


from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekTSSatelliteFactory,
)
from showcase.factories.stransaction_hub_factories import (
    STransactionHubValueDateFactory,
)
from showcase.models.stransaction_sat_models import STransactionSatellite


@dataclass
class STransactionConfig:
    description: str
    min_quantity: float
    max_quantity: float
    min_price: float
    max_price: float


class STransactionChoices(Enum):
    SECURITY_PURCHASE = STransactionConfig(
        "security purchase", 0, 100_000_000, 0.01, 10_000
    )
    SECURITY_SALE = STransactionConfig("security sale", -100_000_000, 0, 0.01, 10_000)
    DIVIDEND_PAYMENT = STransactionConfig("dividend payment", 0, 1_000_000, 0.01, 100)
    FEE_PAYMENT = STransactionConfig("fee payment", -1_000_000, 0, 0.01, 1_000)


class STransactionSatelliteFactory(MontrekTSSatelliteFactory):
    class Meta:
        model = STransactionSatellite
        exclude = ["config"]

    hub_value_date = factory.SubFactory(STransactionHubValueDateFactory)
    stransaction_external_identifier = factory.Faker("ssn")

    @factory.lazy_attribute
    def config(self):
        return random.choice(list(STransactionChoices)).value

    @factory.lazy_attribute
    def stransaction_description(self):
        return self.config.description

    @factory.lazy_attribute
    def stransaction_quantity(self):
        return random.uniform(self.config.min_quantity, self.config.max_quantity)

    @factory.lazy_attribute
    def stransaction_price(self):
        return random.uniform(self.config.min_price, self.config.max_price)
