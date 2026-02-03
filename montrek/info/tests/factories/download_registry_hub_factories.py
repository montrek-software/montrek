import factory

from baseclasses.tests.factories.baseclass_factories import ValueDateListFactory
from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekHubValueDateFactory,
    MontrekHubFactory,
)
from info.models.download_registry_hub_models import DownloadRegistryHub
from info.models.download_registry_hub_models import (
    DownloadRegistryHubValueDate,
)


class DownloadRegistryHubFactory(MontrekHubFactory):
    class Meta:
        model = DownloadRegistryHub


class DownloadRegistryHubValueDateFactory(MontrekHubValueDateFactory):
    class Meta:
        model = DownloadRegistryHubValueDate

    hub = factory.SubFactory(DownloadRegistryHubFactory)
    value_date_list = factory.SubFactory(ValueDateListFactory)
