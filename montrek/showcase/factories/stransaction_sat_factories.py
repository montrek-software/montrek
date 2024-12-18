import random
from dataclasses import dataclass
from enum import Enum

import factory
from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekSatelliteFactory,
)
from file_upload.tests.factories.file_upload_factories import (
    FileUploadRegistryStaticSatelliteFactory,
)

from showcase.factories.stransaction_hub_factories import (
    STransactionFURegistryHubFactory,
    STransactionHubFactory,
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


class STransactionSatelliteFactory(MontrekSatelliteFactory):
    class Meta:
        model = STransactionSatellite
        exclude = ["config"]

    hub_entity = factory.SubFactory(STransactionHubFactory)
    transaction_date = factory.Faker("date")
    transaction_external_identifier = factory.Faker("ssn")

    @factory.lazy_attribute
    def config(self):
        return random.choice(list(STransactionChoices)).value

    @factory.lazy_attribute
    def transaction_description(self):
        return self.config.description

    @factory.lazy_attribute
    def transaction_quantity(self):
        return random.uniform(self.config.min_quantity, self.config.max_quantity)

    @factory.lazy_attribute
    def transaction_price(self):
        return random.uniform(self.config.min_price, self.config.max_price)


class STransactionFURegistryStaticSatelliteFactory(
    FileUploadRegistryStaticSatelliteFactory
):
    class Meta:
        model = "showcase.STransactionFURegistryStaticSatellite"

    hub_entity = factory.SubFactory(STransactionFURegistryHubFactory)
