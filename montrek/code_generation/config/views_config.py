import os

from code_generation.config.base import ConfigBase
from code_generation.config.managers_config import ManagersConfig
from code_generation.config.pages_config import PagesConfig


class ViewsConfig(ConfigBase):
    template_file = "views.py.j2"
    related_config_classes = [ManagersConfig, PagesConfig]

    def get_own_template_context(self):
        list_view_class_name = f"{self.prefix.capitalize()}ListView"
        return {
            "list_view_url_name": f"{self.prefix}_list",
            "list_view_class_name": list_view_class_name,
            "list_view_import": self.get_import_statement(list_view_class_name),
        }

    def get_output_file_path(self):
        return os.path.join(self.app_path, "views", f"{self.prefix}_views.py")
