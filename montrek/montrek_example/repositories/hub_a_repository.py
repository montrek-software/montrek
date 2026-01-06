from baseclasses.repositories.montrek_repository import MontrekRepository
from data_import.api_import.repositories.api_data_import_registry_repositories import (
    ApiDataImportRegistryRepository,
)
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepositoryABC,
)
from montrek_example.models import example_models as me_models
from montrek_example.repositories.hub_b_repository import HubBRepository
from montrek_example.repositories.hub_c_repository import HubCRepository


class HubARepository(MontrekRepository):
    hub_class = me_models.HubA
    default_order_fields = ("hub_id",)

    def set_annotations(self):
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
            ["field_b1_str", "field_b1_date"],
        )

    def get_hub_b_objects(self):
        return HubBRepository().receive()

    def get_hub_c_objects(self):
        return HubCRepository().receive()

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
        return self.receive()


class HubARepository2(MontrekRepository):
    hub_class = me_models.HubA

    def set_annotations(self):
        self.add_linked_satellites_field_annotations(
            me_models.SatC1,
            me_models.LinkHubAHubC,
            ["field_c1_str"],
        )


class HubARepository3(MontrekRepository):
    hub_class = me_models.HubA

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            me_models.SatA1,
            [
                "field_a1_str",
            ],
        )
        self.add_linked_satellites_field_annotations(
            me_models.SatD1,
            me_models.LinkHubCHubD,
            ["field_d1_str"],
            parent_link_classes=(me_models.LinkHubAHubC,),
        )


class HubARepository4(MontrekRepository):
    hub_class = me_models.HubA

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            me_models.SatA4,
            [
                "field_a4_str",
            ],
        )


class HubARepository5(MontrekRepository):
    hub_class = me_models.HubA

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            me_models.SatA5,
            [
                "field_a5_str",
                "secret_field",
            ],
        )


class HubARepository6(MontrekRepository):
    hub_class = me_models.HubA

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            me_models.SatA4,
            [
                "field_a4_str",
            ],
        )
        self.add_satellite_fields_annotations(
            me_models.SatA1,
            ["field_a1_str", "field_a1_int"],
        )


class HubAApiUploadRepository(ApiDataImportRegistryRepository):
    hub_class = me_models.HubAApiUploadRegistryHub
    registry_satellite = me_models.HubAApiUploadRegistryStaticSatellite


class HubAFileUploadRegistryRepository(FileUploadRegistryRepositoryABC):
    hub_class = me_models.HubAFileUploadRegistryHub
    static_satellite_class = me_models.HubAFileUploadRegistryStaticSatellite
    link_file_upload_registry_file_upload_file_class = (
        me_models.LinkHubAFileUploadRegistryFileUploadFile
    )
    link_file_upload_registry_file_log_file_class = (
        me_models.LinkHubAFileUploadRegistryFileLogFile
    )


class HubAJsonRepository(MontrekRepository):
    hub_class = me_models.HubA

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            me_models.SatA3,
            [
                "field_a3_str",
                "field_a3_json",
            ],
        )
