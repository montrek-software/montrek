"""The generated URL sets must not reintroduce ungated entry views.

Every generated app used to get ``lambda _: redirect(...)`` as its entry URL. A
lambda carries no permission gate, so in a restricted app it is a route nobody
checks - reported by the montrek.E003 check, but only once someone starts the
app. Guarded here instead, where it costs a template read.
"""

import pathlib

from django.test import TestCase

from code_generation import CODE_TEMPLATE_DIR

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
