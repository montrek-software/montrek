import os

CODE_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "code_templates")


def get_code_template_path(template_name: str) -> str:
    file_name = f"{template_name}.py.j2"
    return os.path.join(CODE_TEMPLATE_DIR, file_name)
