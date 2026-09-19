"""Guards on the code templates themselves.

Two things the generated-output fixtures cannot tell us. That no URL template
went back to routing a lambda - a lambda carries no permission gate, so in a
restricted app it is a route nobody checks. And that every template binds the
names it uses: the fixtures compare text, so a template using ``views.Foo``
without importing ``views`` produces a fixture that matches perfectly and a
module that raises NameError on import.
"""

import pathlib
import shutil

# Only used to run the resolved ruff binary, see _undefined_names below.
# Bandit reads everything after 'nosec' as test ids, so the reason goes
# here rather than onto the same line.
import subprocess  # noqa: S404  # nosec B404
import tempfile

from django.test import TestCase

from code_generation import CODE_TEMPLATE_DIR
from code_generation.config.code_generation_config import CodeGenerationConfig
from code_generation.rendering import render_template

URL_TEMPLATES = {
    "urls.py.j2": "nav_view_cls_name",
    "registry_urls.py.j2": "registry_nav_view_cls_name",
    "export_registry_urls.py.j2": "export_registry_nav_view_cls_name",
}

VIEW_TEMPLATES = {
    "views.py.j2": "nav_view_cls_name",
    "registry_views.py.j2": "registry_nav_view_cls_name",
    "export_registry_views.py.j2": "export_registry_nav_view_cls_name",
}


def _template(name: str) -> str:
    return (pathlib.Path(CODE_TEMPLATE_DIR) / name).read_text()


class TestUrlTemplatesUseAGatedEntryView(TestCase):
    def test_no_url_template_routes_a_lambda(self):
        for name in URL_TEMPLATES:
            with self.subTest(name):
                self.assertNotIn("lambda", _template(name))

    def test_each_url_template_routes_its_navigation_view(self):
        for name, context_key in URL_TEMPLATES.items():
            with self.subTest(name):
                source = _template(name)
                self.assertIn(f"{{{{ {context_key} }}}}.as_view(", source)

    def test_each_view_template_defines_that_navigation_view(self):
        """The class has to be generated into the app itself - a shared one in
        baseclasses would resolve to that app's access policy."""
        for name, context_key in VIEW_TEMPLATES.items():
            with self.subTest(name):
                source = _template(name)
                self.assertIn(
                    f"class {{{{ {context_key} }}}}"
                    "(views.MontrekNavigationRedirectView):",
                    source,
                )


class TestGeneratedEntryViewNamesAreDistinct(TestCase):
    def test_a_table_and_its_registries_do_not_collide(self):
        from code_generation.config.code_generation_config import (
            CodeGenerationConfig,
        )

        context = CodeGenerationConfig("some/app", "company").context
        names = {
            context["nav_view_cls_name"],
            context["registry_nav_view_cls_name"],
            context["export_registry_nav_view_cls_name"],
        }

        self.assertEqual(len(names), 3)


# Rendered from the start_montrek_app context rather than this one, and covered
# by tests that import the app config they generate.
TEMPLATES_WITH_THEIR_OWN_CONTEXT = {"app_config.py.j2"}


class TestTemplatesBindEveryNameTheyUse(TestCase):
    """Rendered output must have no undefined names.

    The generated-output fixtures compare text, so they happily accept a module
    that cannot be imported. Ruff's F821 answers the question they cannot: is
    every name this module uses actually bound in it?
    """

    def _templates(self):
        for template in sorted(pathlib.Path(CODE_TEMPLATE_DIR).glob("*.py.j2")):
            if template.name not in TEMPLATES_WITH_THEIR_OWN_CONTEXT:
                yield template.name

    def test_no_rendered_template_has_an_undefined_name(self):
        context = CodeGenerationConfig("some/app", "company").context
        for template_name in self._templates():
            with self.subTest(template_name):
                rendered = render_template(template_name, **context)
                self.assertEqual(self._undefined_names(rendered), [])

    def _undefined_names(self, rendered: str) -> list[str]:
        ruff_path = shutil.which("ruff")
        self.assertIsNotNone(ruff_path, "ruff is needed to check the rendered output")
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "rendered.py"
            path.write_text(rendered)
            # Fixed argv: the resolved linter, literal flags and a path this
            # test just wrote. No shell, no caller-supplied arguments.
            result = subprocess.run(  # noqa: S603  # nosec B603
                [ruff_path, "check", "--select", "F821", "--no-cache", str(path)],
                capture_output=True,
                text=True,
                check=False,
            )
        return [line for line in result.stdout.splitlines() if "F821" in line]

    def test_the_guard_notices_a_missing_import(self):
        """Without this, a change that broke the check would look like a pass."""
        context = CodeGenerationConfig("some/app", "company").context
        rendered = render_template("export_registry_views.py.j2", **context)

        without_the_import = rendered.replace("from baseclasses import views\n", "")

        self.assertNotEqual(self._undefined_names(without_the_import), [])
