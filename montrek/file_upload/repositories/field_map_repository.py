from baseclasses.repositories.montrek_repository import MontrekRepository
from baseclasses.typing import SessionDataType
from file_upload.models import (
    FieldMapHub,
    FieldMapHubABC,
    FieldMapStaticSatellite,
    FieldMapStaticSatelliteABC,
)
from django.db.models import F, Q, QuerySet


class FieldMapRepositoryABC(MontrekRepository):
    hub_class = FieldMapHubABC
    static_satellite_class = FieldMapStaticSatelliteABC
    defult_order_fields = ("step", "source_field")

    def __init__(self, session_data: SessionDataType | None = None):
        super().__init__(
            session_data=session_data,
        )
        self._setup_checks()

    def set_annotations(self, **kwargs):
        self.add_satellite_fields_annotations(
            self.static_satellite_class,
            [
                "source_field",
                "database_field",
                "step",
                "function_name",
                "function_parameters",
                "comment",
            ],
            rename_field_map={"comment": "field_map_static_satellite_comment"},
        )

    def get_source_field(self, database_field: str) -> str | None:
        obj = self.receive().filter(database_field=database_field).first()
        if obj is None:
            return None
        return obj.source_field

    def get_all_source_fields(self) -> QuerySet:
        return self.receive().values_list("source_field", flat=True).distinct()

    def get_all_database_fields(self) -> QuerySet:
        return self.receive().values_list("database_field", flat=True).distinct()

    def get_all_intermediate_fields(self) -> QuerySet:
        source_fields = self.get_all_source_fields()
        intermediate_fields = (
            self.receive()
            .filter(database_field__in=(source_fields))
            .filter(~Q(source_field=F("database_field")))
            .values_list("database_field", flat=True)
        )
        return intermediate_fields

    def _setup_checks(self):
        if self.hub_class is FieldMapHubABC:
            raise NotImplementedError(
                "FieldMapRepository class must have hub_class that is derived from FieldMapHubABC"
            )
        if self.static_satellite_class is FieldMapStaticSatelliteABC:
            raise NotImplementedError(
                "FieldMapRepository class must have static_satellite_class that is derived from FieldMapStaticSatelliteABC"
            )


class FieldMapRepository(FieldMapRepositoryABC):
    hub_class = FieldMapHub
    static_satellite_class = FieldMapStaticSatellite
