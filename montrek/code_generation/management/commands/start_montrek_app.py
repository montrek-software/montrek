"""Create a Montrek app.

Wraps Django's ``startapp`` and writes the app config itself, because the access
policy of a new app has to be decided when the app is created rather than left
at whatever the base happens to default to. ``--access`` is therefore required:
``open`` keeps the historical behaviour (a view without ``permission_required``
lets everybody through), ``restricted`` gates every view in the app. See
``baseclasses.access``.
"""

import os
import shutil

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.utils.module_loading import import_string

from baseclasses.access import AccessKind
from baseclasses.app_config import find_namespace_base
from code_generation.rendering import format_python_file, render_template

APP_CONFIG_TEMPLATE = "app_config.py.j2"

ACCESS_OPEN = "open"
ACCESS_RESTRICTED = "restricted"

# The permission enums name their members after the access kinds, see e.g.
# RiskContributorPermissions. A restricted app has to cover all four, otherwise
# views of the uncovered kind deny everybody.
PERMISSION_MEMBER_NAMES = {
    AccessKind.VIEW: "CAN_VIEW",
    AccessKind.CREATE: "CAN_CREATE",
    AccessKind.UPDATE: "CAN_UPDATE",
    AccessKind.DELETE: "CAN_DELETE",
}


class Command(BaseCommand):
    help = "Create a Montrek app and decide its access policy."

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        self.base_path: str = "."
        self.app_path: str = ""
        self.app_name: str = ""
        super().__init__(stdout, stderr, no_color, force_color)

    def add_arguments(self, parser):
        parser.add_argument(
            "name",
            type=str,
            help="Name of the new app.",
        )
        parser.add_argument(
            "-p",
            "--path",
            type=str,
            default=".",
            metavar="DIR",
            help="Path of repository in which to generate the new app.",
        )
        parser.add_argument(
            "--access",
            type=str,
            required=True,
            choices=[ACCESS_OPEN, ACCESS_RESTRICTED],
            help=(
                "Access policy of the new app. 'open' lets every view through "
                "unless it declares a permission of its own; 'restricted' "
                "requires a permission for every view."
            ),
        )
        parser.add_argument(
            "--permissions",
            type=str,
            default="",
            metavar="DOTTED_PATH",
            help=(
                "Dotted path to the permission enum a restricted app outside "
                "any restricted subtree uses, e.g. "
                "'my_app.user_groups.constants.MyPermissions'."
            ),
        )

    def handle(self, *args, **kwargs):
        # Normalize inputs
        self.base_path = kwargs["path"]
        self.app_name = kwargs["name"].lower()

        # Where the app will ultimately live
        self.app_path = os.path.join(self.base_path, self.app_name)

        # 1) Work out the app config before anything is written, so a rejected
        #    access policy does not leave a half-created app behind.
        app_config_source = self._render_app_config(
            access=kwargs["access"],
            permissions_path=kwargs["permissions"],
        )

        # 2) Create the app in the current working directory
        self._start_app()

        # 3) Move it if a subfolder path was provided
        self._move_app()

        # 4) Write the app config, replacing the one startapp produced
        self._write_app_config(app_config_source)

        # 5) Remove files we don't want
        self._remove_files()

    @property
    def dotted_app_path(self) -> str:
        dotted_base = os.path.normpath(self.base_path)
        if dotted_base in (".", ""):
            return self.app_name
        return f"{dotted_base.replace(os.sep, '.')}.{self.app_name}"

    @property
    def config_cls_name(self) -> str:
        # Same spelling Django's own startapp template uses.
        camel_case_name = "".join(
            part.capitalize() for part in self.app_name.split("_")
        )
        return f"{camel_case_name}Config"

    def _render_app_config(self, access: str, permissions_path: str) -> str:
        is_restricted = access == ACCESS_RESTRICTED
        namespace_base = (
            find_namespace_base(self.dotted_app_path) if is_restricted else None
        )
        if not is_restricted and permissions_path:
            raise CommandError("--permissions only applies to '--access restricted'.")
        if namespace_base is not None and permissions_path:
            raise CommandError(
                f"{self.dotted_app_path!r} lies inside the subtree owned by "
                f"{namespace_base.__name__}, which already declares the "
                f"permissions for its apps. Drop --permissions."
            )
        context = {
            "app_dotted_path": self.dotted_app_path,
            "config_cls_name": self.config_cls_name,
            "is_restricted": is_restricted,
            "base_cls_name": "MontrekAppConfig",
            "namespace_base_cls_name": "",
            "namespace_base_module": "",
            "namespace": "",
            "permissions_module": "",
            "permissions_cls_name": "",
        }
        if namespace_base is not None:
            context.update(
                base_cls_name=namespace_base.__name__,
                namespace_base_cls_name=namespace_base.__name__,
                namespace_base_module=namespace_base.__module__,
                namespace=namespace_base.namespace,
            )
        elif is_restricted:
            permissions_module, permissions_cls_name = self._validated_permissions(
                permissions_path
            )
            context.update(
                permissions_module=permissions_module,
                permissions_cls_name=permissions_cls_name,
            )
        return render_template(APP_CONFIG_TEMPLATE, **context)

    def _validated_permissions(self, permissions_path: str) -> tuple[str, str]:
        """Resolve --permissions and make sure it covers every access kind."""
        if not permissions_path:
            raise CommandError(
                f"'--access restricted' needs permissions: {self.dotted_app_path!r} "
                f"lies outside every restricted subtree, so it cannot inherit "
                f"them. Pass --permissions with the dotted path to the app's "
                f"permission enum."
            )
        try:
            permission_enum = import_string(permissions_path)
        except ImportError as error:
            raise CommandError(
                f"Could not import the permission enum {permissions_path!r}: {error}"
            ) from error
        missing = [
            member_name
            for member_name in PERMISSION_MEMBER_NAMES.values()
            if getattr(permission_enum, member_name, None) is None
        ]
        if missing:
            raise CommandError(
                f"{permissions_path!r} is missing {', '.join(missing)}. A "
                f"restricted app needs one permission per access kind "
                f"({', '.join(kind.value for kind in PERMISSION_MEMBER_NAMES)}), "
                f"otherwise views of the uncovered kind deny everybody."
            )
        without_codename = [
            member_name
            for member_name in PERMISSION_MEMBER_NAMES.values()
            if not getattr(
                getattr(permission_enum, member_name), "namespaced_codename", ""
            )
        ]
        if without_codename:
            raise CommandError(
                f"{', '.join(without_codename)} of {permissions_path!r} have no "
                f"'namespaced_codename'. Follow the shape of the existing "
                f"permission enums."
            )
        module, _, class_name = permissions_path.rpartition(".")
        return module, class_name

    def _start_app(self):
        call_command("startapp", self.app_name)

    def _move_app(self):
        # Only move if target path is not the current directory
        if os.path.normpath(self.base_path) != os.path.normpath("."):
            os.makedirs(self.base_path, exist_ok=True)
            shutil.move(self.app_name, self.base_path)

    def _write_app_config(self, app_config_source: str):
        apps_py = os.path.join(self.app_path, "apps.py")
        with open(apps_py, "w", encoding="utf-8") as f:
            f.write(app_config_source)
        message = format_python_file(apps_py)
        if message:
            self.stdout.write(self.style.WARNING(message))
        self.stdout.write(self.style.SUCCESS(f"Wrote app config at '{apps_py}'."))

    def _remove_files(self):
        remove_files = ("tests.py", "models.py", "views.py")
        for rm_file in remove_files:
            path = os.path.join(self.app_path, rm_file)
            if os.path.exists(path):
                os.remove(path)
