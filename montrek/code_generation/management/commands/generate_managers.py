from code_generation.management.base.class_definition_command import (
    CodeGenerationCommandBase,
)
from code_generation.config.managers_config import ManagersConfig


class Command(CodeGenerationCommandBase):
    config_class = ManagersConfig
