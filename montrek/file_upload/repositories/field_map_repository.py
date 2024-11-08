from baseclasses.repositories.montrek_repository import MontrekRepository
from file_upload.models import (
    FieldMapHub,
    FieldMapHubABC,
    FieldMapStaticSatellite,
    FieldMapStaticSatelliteABC,
)
from django.db.models import Q, F


class FieldMapRepositoryABC(MontrekRepository):
    hub_class = FieldMapHubABC
    static_satellite_class = FieldMapStaticSatelliteABC

    def __init__(self, session_data={}):
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
        )
        self.rename_field("comment", "field_map_static_satellite_comment")
        queryset = self.build_queryset()
        return queryset.order_by("step", "source_field")

    def get_source_field(self, database_field: str) -> str | None:
        objs = self.std_queryset().filter(database_field=database_field)
        if len(objs) == 0:
            return None
        return objs.first().source_field

    def get_all_source_fields(self) -> list[str]:
        return self.std_queryset().values_list("source_field", flat=True).distinct()

    def get_all_database_fields(self) -> list[str]:
        return self.std_queryset().values_list("database_field", flat=True).distinct()

    def get_all_intermediate_fields(self) -> list[str]:
        source_fields = self.get_all_source_fields()
        intermediate_fields = (
            self.std_queryset()
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
