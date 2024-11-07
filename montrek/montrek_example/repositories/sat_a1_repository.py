from baseclasses.repositories.montrek_repository import MontrekRepository
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepository,
)
from file_upload.repositories.field_map_repository import FieldMapRepositoryABC
from montrek_example import models as me_models


class SatA1Repository(MontrekRepository):
    hub_class = me_models.HubA

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            me_models.SatA1,
            [
                "field_a1_int",
                "field_a1_str",
            ],
        )

    def get_upload_registry_table(self):
        return (
            FileUploadRegistryRepository()
            .std_queryset()
            .filter(link_file_upload_registry_hub_a__in=self.std_queryset())
            .distinct()
            .order_by("-created_at")
        )


class SatA1FieldMapRepository(FieldMapRepositoryABC):
    hub_class = me_models.SatA1FieldMapHub
    static_satellite_class = me_models.SatA1FieldMapStaticSatellite
