import factory
from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekSatelliteFactory,
)
from data_import.base.models import (
    DataImportRegistryBaseSatelliteABC,
)


class DataImportRegistryBaseSatelliteFactory(MontrekSatelliteFactory):
    class Meta:
        model = DataImportRegistryBaseSatelliteABC

    import_status = DataImportRegistryBaseSatelliteABC.ImportStatus.PROCESSED.value
    import_message = factory.Faker("sentence")
