import os

from code_generation.management.base.class_definition_command import (
    ClassDefinitionCommandBase,
)


class Command(ClassDefinitionCommandBase):
    template_file: str = "repositories.py.j2"
    class_suffix: str = "repository"

    def get_output_path_in_app(self, prefix: str) -> str:
        file_name = f"{prefix}_{self.class_suffix}_models.py"
        return os.path.join("models", file_name)
