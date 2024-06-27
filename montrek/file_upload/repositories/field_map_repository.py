from baseclasses.repositories.montrek_repository import MontrekRepository
from file_upload.models import (
    FieldMapHub,
    FieldMapHubABC,
    FieldMapStaticSatellite,
    FieldMapStaticSatelliteABC,
)


class FieldMapRepositoryABC(MontrekRepository):
    hub_class = FieldMapHubABC
    static_satellite_class = FieldMapStaticSatelliteABC

    def __init__(self, session_data={}):
        super().__init__(
            session_data=session_data,
        )
        self._setup_checks()

    def std_queryset(self, **kwargs):
        self.add_satellite_fields_annotations(
            self.static_satellite_class,
            [
                "source_field",
                "database_field",
                "function_name",
                "function_parameters",
                "comment",
            ],
        )
        self.rename_field("comment", "field_map_static_satellite_comment")
        self.annotations.pop("comment")
        queryset = self.build_queryset()
        return queryset.order_by("source_field")

    def get_source_field(self, database_field: str) -> str:
        obj = self.std_queryset().filter(database_field=database_field).get()
        return obj.source_field

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
