from baseclasses.repositories.montrek_repository import MontrekRepository
from file_upload.models import FieldMapHub, FieldMapStaticSatellite


class FieldMapRepository(MontrekRepository):
    hub_class = FieldMapHub

    def std_queryset(self, **kwargs):
        self.add_satellite_fields_annotations(
            FieldMapStaticSatellite,
            ["source_field", "database_field", "function_name"],
        )
        queryset = self.build_queryset()
        return queryset
