from code_generation.management.base.class_definition_command import (
    CodeGenerationCommandBase,
)
from code_generation.config.hub_models_config import HubModelsConfig


class Command(CodeGenerationCommandBase):
    config_class = HubModelsConfig
