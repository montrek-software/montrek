import os

from code_generation.management.base.class_definition_command import (
    ClassDefinitionCommandBase,
)


class Command(ClassDefinitionCommandBase):
    template_file: str = "hub_models.py.j2"

    def get_file_path_within_app(self, prefix: str) -> str:
        file_name = f"{prefix}_hub_models.py"
        return os.path.join("models", file_name)
