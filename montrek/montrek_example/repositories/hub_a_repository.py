from baseclasses.repositories.montrek_repository import MontrekRepository
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepositoryABC,
)
from montrek_example import models as me_models
from montrek_example.repositories.hub_b_repository import HubBRepository
from api_upload.repositories.api_upload_registry_repository import (
    ApiUploadRepository,
)


class HubARepository(MontrekRepository):
    hub_class = me_models.HubA

    def std_queryset(self):
        self.add_satellite_fields_annotations(
            me_models.SatA1,
            [
                "field_a1_int",
                "field_a1_str",
            ],
        )
        self.add_satellite_fields_annotations(
            me_models.SatA2,
            [
                "field_a2_float",
                "field_a2_str",
            ],
        )
        self.add_linked_satellites_field_annotations(
            me_models.SatB1,
            me_models.LinkHubAHubB,
            ["field_b1_str"],
        )
        return self.build_queryset()

    def get_hub_b_objects(self):
        return HubBRepository().std_queryset()

    def test_queryset_1(self):
        self.add_satellite_fields_annotations(
            me_models.SatA1,
            [
                "field_a1_int",
            ],
        )
        self.add_satellite_fields_annotations(
            me_models.SatA2,
            [
                "field_a2_float",
            ],
        )
        return self.build_queryset()

    def test_queryset_2(self):
        self.add_linked_satellites_field_annotations(
            me_models.SatB1,
            me_models.LinkHubAHubB,
            ["field_b1_str"],
        )
        return self.build_queryset()


class HubAUploadRepository(MontrekRepository):
    hub_class = me_models.HubA

    def std_queryset(self):
        return (
            ApiUploadRepository()
            .std_queryset()
            .filter(link_api_upload_registry_hub_a__in=HubARepository().std_queryset())
            .distinct()
            .order_by("-created_at")
        )


class HubAFileUploadRegistryRepository(FileUploadRegistryRepositoryABC):
    hub_class = me_models.HubAFileUploadRegistryHub
    static_satellite_class = me_models.HubAFileUploadRegistryStaticSatellite
    link_file_upload_registry_file_upload_file_class = (
        me_models.LinkHubAFileUploadRegistryFileUploadFile
    )
