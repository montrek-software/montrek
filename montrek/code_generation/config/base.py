class ConfigBase:
    template_file: str = ""
    related_config_classes = []

    def __init__(self, app_path, prefix):
        self.app_path: str = app_path
        self.prefix: str = prefix

    def get_output_file_path(self) -> str:
        return ""

    def get_import_statement(self, class_name: str) -> str:
        output_file_path = self.get_output_file_path()
        dotted_output_file_path = output_file_path.replace("/", ".")
        dotted_output_file_path = dotted_output_file_path.replace(".py", "")
        return f"from {dotted_output_file_path} import {class_name}"

    def get_own_template_context(self) -> dict[str, str]:
        return {}

    def get_template_context(self) -> dict[str, str]:
        context = {**self.get_own_template_context()}
        for related_config_class in self.related_config_classes:
            related_config = related_config_class(self.app_path, self.prefix)
            context.update(related_config.get_template_context())
        return context
