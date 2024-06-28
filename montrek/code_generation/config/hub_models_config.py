import os

from code_generation.config.base import ConfigBase


class HubModelsConfig(ConfigBase):
    template_file = "hub_models.py.j2"

    def get_template_context(self):
        class_name = f"{self.prefix.capitalize()}Hub"
        return {
            "hub_class_name": class_name,
            "hub_model_import": self.get_import_statement(class_name),
        }

    def get_output_file_path(self):
        return os.path.join(self.app_path, "models", f"{self.prefix}_hub_models.py")
