import os

from code_generation.config.base import ConfigBase
from code_generation.config.hub_models_config import HubModelsConfig


class SatelliteModelsConfig(ConfigBase):
    template_file = "satellite_models.py.j2"
    related_config_classes = [HubModelsConfig]

    def get_own_template_context(self):
        class_name = f"{self.prefix.capitalize()}Satellite"
        return {
            "satellite_class_name": class_name,
            "satellite_model_import": self.get_import_statement(class_name),
        }

    def get_output_file_path(self):
        return os.path.join(
            self.app_path, "models", f"{self.prefix}_satellite_models.py"
        )
