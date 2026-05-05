from process_pipeline.repositories.process_pipeline_repositories import (
    ProcessPipelineRepositoryABC,
)


class RegistryRepositoryABC(ProcessPipelineRepositoryABC):
    registry_fields = [
        "import_status",
        "import_message",
    ]
