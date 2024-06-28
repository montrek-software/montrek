from code_generation.management.base.class_definition_command import (
    CodeGenerationCommandBase,
)
from code_generation.config.pages_config import PagesConfig


class Command(CodeGenerationCommandBase):
    config_class = PagesConfig
