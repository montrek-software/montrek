import os

from code_generation.config.base import ConfigBase
from code_generation.config.satellite_models_config import SatelliteModelsConfig


class RepositoriesConfig(ConfigBase):
    template_file = "repositories.py.j2"
    related_config_classes = [SatelliteModelsConfig]

    def get_own_template_context(self):
        class_name = f"{self.prefix.capitalize()}Repository"
        return {
            "repository_class_name": class_name,
            "repository_import": self.get_import_statement(class_name),
        }

    def get_output_file_path(self):
        return os.path.join(
            self.app_path, "repositories", f"{self.prefix}_repositories.py"
        )
