from process_pipeline.repositories.pipeline_registry_repositories import (
    PipelineRegistryRepositoryABC,
)


class RegistryRepositoryABC(PipelineRegistryRepositoryABC):
    registry_fields = [
        "import_status",
        "import_message",
    ]
