import factory
from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekSatelliteFactory,
)
from data_import.base.constants import ImportStatus
from data_import.base.models import (
    DataImportRegistryBaseSatelliteABC,
)


class DataImportRegistryBaseSatelliteFactory(MontrekSatelliteFactory):
    class Meta:
        model = DataImportRegistryBaseSatelliteABC

    import_status = ImportStatus.PROCESSED.value.label
    import_message = factory.Faker("sentence")
