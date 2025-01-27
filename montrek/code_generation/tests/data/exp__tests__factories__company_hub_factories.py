import factory

from baseclasses.tests.factories.baseclass_factories import ValueDateListFactory
from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekHubValueDateFactory,
    MontrekHubFactory,
)
from .users.vincentmohiuddin.code.montrek.montrek.code_generation.tests.data.output.models.company_hub_models import (
    CompanyHub,
)
from .users.vincentmohiuddin.code.montrek.montrek.code_generation.tests.data.output.models.company_hub_models import (
    CompanyHubValueDate,
)


class CompanyHubFactory(MontrekHubFactory):
    class Meta:
        model = CompanyHub


class CompanyHubValueDateFactory(MontrekHubValueDateFactory):
    class Meta:
        model = CompanyHubValueDate

    hub = factory.SubFactory(CompanyHubFactory)
    value_date_list = factory.SubFactory(ValueDateListFactory)
