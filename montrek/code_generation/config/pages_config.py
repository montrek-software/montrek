import os

from code_generation.config.base import ConfigBase


class PagesConfig(ConfigBase):
    template_file = "pages.py.j2"
    related_config_classes = []

    def get_own_template_context(self):
        class_name = f"{self.prefix.capitalize()}Page"
        return {
            "page_class_name": class_name,
            "page_import": self.get_import_statement(class_name),
            "page_title": f"{self.prefix.capitalize()}",
            "list_view_title": f"{self.prefix.capitalize()} List",
            "list_tab_name": f"{self.prefix.capitalize()} List",
            "list_tab_id": f"tab_{self.prefix}_list",
            "list_url_name": f"{self.prefix}_list",
        }

    def get_output_file_path(self):
        return os.path.join(self.app_path, "pages", f"{self.prefix}_pages.py")
