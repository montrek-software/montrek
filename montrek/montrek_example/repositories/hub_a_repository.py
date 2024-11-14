from baseclasses.repositories.montrek_repository import MontrekRepository
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepositoryABC,
)
from montrek_example import models as me_models
from montrek_example.repositories.hub_b_repository import HubBRepository
from api_upload.repositories.api_upload_registry_repository import (
    ApiUploadRepositoryABC,
)


class HubARepository(MontrekRepository):
    hub_class = me_models.HubA

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
            ["field_b1_str"],
        )

    def get_hub_b_objects(self):
        return HubBRepository().receive()

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
            me_models.SatB1,
            me_models.LinkHubAHubB,
            ["field_b1_str"],
        )


class HubAApiUploadRepository(ApiUploadRepositoryABC):
    hub_class = me_models.HubAApiUploadRegistryHub
    static_satellite_class = me_models.HubAApiUploadRegistryStaticSatellite


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
