import os

from code_generation.config.base import ConfigBase
from code_generation.config.repositories_config import RepositoriesConfig


class ManagersConfig(ConfigBase):
    template_file = "managers.py.j2"
    related_config_classes = [RepositoriesConfig]

    def get_own_template_context(self):
        class_name = f"{self.prefix.capitalize()}Manager"
        return {
            "manager_class_name": class_name,
            "manager_import": self.get_import_statement(class_name),
        }

    def get_output_file_path(self):
        return os.path.join(self.app_path, "managers", f"{self.prefix}_managers.py")
