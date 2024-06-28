from code_generation.management.base.class_definition_command import (
    CodeGenerationCommandBase,
)
from code_generation.config.views_config import ViewsConfig


class Command(CodeGenerationCommandBase):
    config_class = ViewsConfig
