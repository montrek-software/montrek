import factory
from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekHubFactory,
    MontrekHubValueDateFactory,
    ValueDateListFactory,
)
from showcase.models.sproduct_hub_models import SProductHub, SProductHubValueDate


class SProductHubFactory(MontrekHubFactory):
    class Meta:
        model = SProductHub


class SProductHubValueDateFactory(MontrekHubValueDateFactory):
    class Meta:
        model = SProductHubValueDate

    hub = factory.SubFactory(SProductHubFactory)
    value_date_list = factory.SubFactory(ValueDateListFactory)
