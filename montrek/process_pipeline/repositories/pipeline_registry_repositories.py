from baseclasses.repositories.montrek_repository import MontrekRepository
from process_pipeline.models.pipeline_registry_sat_models import (
    PipelineRegistrySatelliteABC,
)


class PipelineRegistryRepositoryABC(MontrekRepository):
    registry_satellite: type[PipelineRegistrySatelliteABC]
    registry_fields: list[str]
    default_order_fields = ("-created_at",)

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            self.registry_satellite,
            [
                "created_at",
                "celery_task_id",
            ]
            + self.registry_fields,
        )
