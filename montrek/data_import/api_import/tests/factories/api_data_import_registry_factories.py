from data_import.base.tests.factories.data_import_registry_factories import DataImportRegistryBaseSatelliteFactory
from data_import.api_import.models.api_registry_sat_models import ApiRegistrySatellite
import factory

class ApiDataImportRegistryBaseSatelliteFactory(DataImportRegistryBaseSatelliteFactory):
    class Meta:
        model = ApiRegistrySatellite
    import_url = factory.Faker("url")
