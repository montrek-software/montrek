from data_import.base.tests.factories.data_import_registry_factories import DataImportRegistryBaseSatelliteFactory
from data_import.api_import.models.api_registry_sat_models import MockApiRegistrySatellite
import factory

class ApiDataImportRegistryBaseSatelliteFactory(DataImportRegistryBaseSatelliteFactory):
    class Meta:
        model = MockApiRegistrySatellite
    import_url = factory.Faker("url")
