import factory
from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekHubFactory,
    MontrekHubValueDateFactory,
    ValueDateListFactory,
)
from showcase.models.product_hub_models import ProductHub, ProductHubValueDate


class ProductHubFactory(MontrekHubFactory):
    class Meta:
        model = ProductHub


class ProductHubValueDateFactory(MontrekHubValueDateFactory):
    class Meta:
        model = ProductHubValueDate

    hub = factory.SubFactory(ProductHubFactory)
    value_date_list = factory.SubFactory(ValueDateListFactory)
