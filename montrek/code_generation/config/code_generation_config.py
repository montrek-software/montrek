import os
import re


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
            "forms": "forms.py.j2",
            "hub_factories": "hub_factories.py.j2",
            "hub_models": "hub_models.py.j2",
            "managers": "managers.py.j2",
            "models_init": "models_init.py.j2",
            "pages": "pages.py.j2",
            "repositories": "repositories.py.j2",
            "sat_factories": "sat_factories.py.j2",
            "sat_models": "sat_models.py.j2",
            "urls": "urls.py.j2",
            "urls_init": "urls_init.py.j2",
            "views": "views.py.j2",
            "views_init": "views_init.py.j2",
            "view_tests": "view_tests.py.j2",
        }

        self.output_paths = {
            "forms": ["forms", f"{prefix}_forms.py"],
            "hub_factories": ["tests", "factories", f"{prefix}_hub_factories.py"],
            "hub_models": ["models", f"{prefix}_hub_models.py"],
            "managers": ["managers", f"{prefix}_managers.py"],
            "models_init": ["models", "__init__.py"],
            "pages": ["pages", f"{prefix}_pages.py"],
            "repositories": ["repositories", f"{prefix}_repositories.py"],
            "sat_models": ["models", f"{prefix}_sat_models.py"],
            "sat_factories": ["tests", "factories", f"{prefix}_sat_factories.py"],
            "urls": ["urls", f"{prefix}_urls.py"],
            "urls_init": ["urls", "__init__.py"],
            "views": ["views", f"{prefix}_views.py"],
            "views_init": ["views", "__init__.py"],
            "view_tests": ["tests", "views", f"test_{prefix}_views.py"],
        }
        self.output_paths = {
            k: os.path.join(self.app_path, *v) for k, v in self.output_paths.items()
        }
        c_prefix = self._prefix_to_camel_case(prefix)
        ui_prefix = prefix.replace("_", " ").title()

        hub_cls_name = f"{c_prefix}Hub"
        hub_factory_cls_name = f"{hub_cls_name}Factory"
        hub_value_date_cls_name = f"{hub_cls_name}ValueDate"
        hub_value_date_factory_cls_name = f"{hub_value_date_cls_name}Factory"
        list_view_cls_name = f"{c_prefix}ListView"
        create_view_cls_name = f"{c_prefix}CreateView"
        create_form_cls_name = f"{c_prefix}CreateForm"
        update_view_cls_name = f"{c_prefix}UpdateView"
        delete_view_cls_name = f"{c_prefix}DeleteView"
        detail_view_cls_name = f"{c_prefix}DetailView"
        manager_cls_name = f"{c_prefix}TableManager"
        details_manager_cls_name = f"{c_prefix}DetailsManager"
        page_cls_name = f"{c_prefix}Page"
        details_page_cls_name = f"{c_prefix}DetailsPage"
        repo_cls_name = f"{c_prefix}Repository"
        sat_cls_name = f"{c_prefix}Satellite"
        sat_factory_cls_name = f"{sat_cls_name}Factory"

        self.context = {
            "create_action_hover": f"Create new {ui_prefix}",
            "create_action_id": f"id_create_{prefix}",
            "create_form_cls_import": self._get_import("forms", create_form_cls_name),
            "create_form_cls_name": create_form_cls_name,
            "create_tab_id": f"tab_{prefix}_create",
            "create_tab_name": f"{ui_prefix}",
            "create_view_cls_import": self._get_import("views", create_view_cls_name),
            "create_view_cls_import_rel": f"from .{prefix}_views import {create_view_cls_name}",
            "create_view_cls_name": create_view_cls_name,
            "create_view_test_cls_name": f"Test{c_prefix}CreateView",
            "create_view_title": f"{ui_prefix} Create",
            "create_view_url": f"{prefix}/create",
            "create_view_url_name": f"{prefix}_create",
            "delete_hover": f"Delete {ui_prefix}",
            "delete_tab_id": f"tab_{prefix}_delete",
            "delete_tab_name": f"{ui_prefix}",
            "delete_view_cls_import": self._get_import("views", delete_view_cls_name),
            "delete_view_cls_import_rel": f"from .{prefix}_views import {delete_view_cls_name}",
            "delete_view_cls_name": delete_view_cls_name,
            "delete_view_test_cls_name": f"Test{c_prefix}DeleteView",
            "delete_view_title": f"{ui_prefix} Delete",
            "delete_view_url": f"{prefix}/<int:pk>/delete",
            "delete_view_url_name": f"{prefix}_delete",
            "detail_tab_id": f"tab_{prefix}_details",
            "details_tab_name": f"{ui_prefix}",
            "detail_view_cls_import": self._get_import("views", detail_view_cls_name),
            "detail_view_cls_import_rel": f"from .{prefix}_views import {detail_view_cls_name}",
            "detail_view_cls_name": detail_view_cls_name,
            "detail_view_test_cls_name": f"Test{c_prefix}DetailView",
            "detail_view_title": f"{ui_prefix} Details",
            "detail_view_url": f"{prefix}/<int:pk>/details",
            "detail_view_url_name": f"{prefix}_details",
            "details_hover": f"View {ui_prefix} Details",
            "details_manager_cls_import": self._get_import(
                "managers", details_manager_cls_name
            ),
            "details_manager_cls_name": details_manager_cls_name,
            "details_page_cls_import": self._get_import("pages", details_page_cls_name),
            "details_page_cls_name": details_page_cls_name,
            "details_page_title": f"{ui_prefix} Details",
            "hub_cls_import": self._get_import("hub_models", hub_cls_name),
            "hub_cls_import_rel": f"from .{prefix}_hub_models import {hub_cls_name}",
            "hub_cls_name": hub_cls_name,
            "hub_factory_cls_import": self._get_import(
                "hub_factories", hub_factory_cls_name
            ),
            "hub_factory_cls_name": hub_factory_cls_name,
            "hub_value_date_cls_import": self._get_import(
                "hub_models", hub_value_date_cls_name
            ),
            "hub_value_date_cls_import_rel": f"from .{prefix}_hub_models import {hub_value_date_cls_name}",
            "hub_value_date_cls_name": hub_value_date_cls_name,
            "hub_value_date_factory_cls_import": self._get_import(
                "hub_factories", hub_value_date_factory_cls_name
            ),
            "hub_value_date_factory_cls_name": hub_value_date_factory_cls_name,
            "list_tab_id": f"tab_{prefix}_list",
            "list_tab_name": f"{ui_prefix}",
            "list_view_cls_import": self._get_import("views", list_view_cls_name),
            "list_view_cls_import_rel": f"from .{prefix}_views import {list_view_cls_name}",
            "list_view_cls_name": list_view_cls_name,
            "list_view_test_cls_name": f"Test{c_prefix}ListView",
            "list_view_title": f"{ui_prefix} List",
            "list_view_url": f"{prefix}/list",
            "list_view_url_name": f"{prefix}_list",
            "manager_cls_import": self._get_import("managers", manager_cls_name),
            "manager_cls_name": manager_cls_name,
            "page_cls_import": self._get_import("pages", page_cls_name),
            "page_cls_name": page_cls_name,
            "page_title": ui_prefix,
            "prefix": prefix,
            "repo_cls_import": self._get_import("repositories", repo_cls_name),
            "repo_cls_name": repo_cls_name,
            "sat_cls_import": self._get_import("sat_models", sat_cls_name),
            "sat_cls_import_rel": f"from .{prefix}_sat_models import {sat_cls_name}",
            "sat_cls_name": sat_cls_name,
            "sat_factory_cls_import": self._get_import(
                "sat_factories", sat_factory_cls_name
            ),
            "sat_factory_cls_name": sat_factory_cls_name,
            "update_hover": f"Update {ui_prefix}",
            "update_tab_id": f"tab_{prefix}_update",
            "update_tab_name": f"{ui_prefix}",
            "update_view_cls_import": self._get_import("views", update_view_cls_name),
            "update_view_cls_import_rel": f"from .{prefix}_views import {update_view_cls_name}",
            "update_view_cls_name": update_view_cls_name,
            "update_view_test_cls_name": f"Test{c_prefix}UpdateView",
            "update_view_title": f"{ui_prefix} Update",
            "update_view_url": f"{prefix}/<int:pk>/update",
            "update_view_url_name": f"{prefix}_update",
            "urlpatterns_import_rel": f"from .{prefix}_urls import urlpatterns",
        }

    def _get_import(self, key: str, class_name: str) -> str:
        path = self.output_paths[key]
        dotted_path = path.replace("/", ".")
        dotted_path = dotted_path.replace(".py", "")
        return f"from {dotted_path} import {class_name}"

    def _prefix_to_camel_case(self, prefix: str) -> str:
        # Use regular expressions to find underscores followed by a letter and remove the underscore, capitalizing the letter
        prefix = re.sub(r"_([a-z])", lambda match: match.group(1).upper(), prefix)
        return prefix[0].upper() + prefix[1:]
