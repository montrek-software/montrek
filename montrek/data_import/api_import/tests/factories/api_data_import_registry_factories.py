from data_import.base.models import TestApiRegistrySatellite
from data_import.base.tests.factories.data_import_registry_factories import (
    DataImportRegistryBaseSatelliteFactory,
)

import factory


class ApiDataImportRegistryBaseSatelliteFactory(DataImportRegistryBaseSatelliteFactory):
    class Meta:
        model = TestApiRegistrySatellite

    import_url = factory.Faker("url")
