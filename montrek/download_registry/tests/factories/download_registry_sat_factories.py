import factory
from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekSatelliteFactory,
)

from download_registry.tests.factories.download_registry_hub_factories import (
    DownloadRegistryHubFactory,
)
from download_registry.models.download_registry_sat_models import (
    DownloadRegistrySatellite,
)


class DownloadRegistrySatelliteFactory(MontrekSatelliteFactory):
    class Meta:
        model = DownloadRegistrySatellite

    hub_entity = factory.SubFactory(DownloadRegistryHubFactory)
