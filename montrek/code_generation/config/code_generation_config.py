import os


class CodeGenerationConfig:
    app_path: str
    prefix: str
    template_files: dict[str, str]
    output_paths: dict[str, str]
    context: dict[str, str]

    def __init__(self, app_path, prefix):
        self.app_path = app_path
        self.prefix = prefix

        self.template_files = {
            "hub_models": "hub_models.py.j2",
            "sat_models": "sat_models.py.j2",
            "models_init": "models_init.py.j2",
            "repositories": "repositories.py.j2",
            "managers": "managers.py.j2",
            "pages": "pages.py.j2",
            "urls": "urls.py.j2",
            "views": "views.py.j2",
        }

        self.output_paths = {
            "hub_models": os.path.join("models", f"{prefix}_hub_models.py"),
            "sat_models": os.path.join("models", f"{prefix}_sat_models.py"),
            "models_init": os.path.join("models", "__init__.py"),
            "repositories": os.path.join("repositories", f"{prefix}_repositories.py"),
            "managers": os.path.join("managers", f"{prefix}_managers.py"),
            "pages": os.path.join("views", f"{prefix}_pages.py"),
            "urls": os.path.join("urls", f"{prefix}_urls.py"),
            "views": os.path.join("views", f"{prefix}_views.py"),
        }
        self.output_paths = {
            k: os.path.join(self.app_path, v) for k, v in self.output_paths.items()
        }
        c_prefix = prefix.capitalize()

        hub_cls_name = f"{c_prefix}Hub"
        list_view_cls_name = f"{c_prefix}ListView"
        manager_cls_name = f"{c_prefix}TableManager"
        page_cls_name = f"{c_prefix}Page"
        repo_cls_name = f"{c_prefix}Repository"
        sat_cls_name = f"{c_prefix}Satellite"

        self.context = {
            "hub_cls_import": self._get_import("hub_models", hub_cls_name),
            "hub_cls_name": hub_cls_name,
            "list_tab_id": f"tab_{prefix}_list",
            "list_tab_name": f"{c_prefix} List",
            "list_view_cls_import": self._get_import("views", list_view_cls_name),
            "list_view_cls_name": list_view_cls_name,
            "list_view_title": f"{c_prefix} List",
            "list_view_url": f"{prefix}/list",
            "list_view_url_name": f"{prefix}_list",
            "manager_cls_import": self._get_import("managers", manager_cls_name),
            "manager_cls_name": manager_cls_name,
            "page_cls_import": self._get_import("pages", page_cls_name),
            "page_cls_name": page_cls_name,
            "page_title": c_prefix,
            "repo_cls_import": self._get_import("repositories", repo_cls_name),
            "repo_cls_name": repo_cls_name,
            "sat_cls_import": self._get_import("sat_models", sat_cls_name),
            "sat_cls_name": sat_cls_name,
        }

    def _get_import(self, key: str, class_name: str) -> str:
        path = self.output_paths[key]
        dotted_path = path.replace("/", ".")
        dotted_path = dotted_path.replace(".py", "")
        return f"from {dotted_path} import {class_name}"
