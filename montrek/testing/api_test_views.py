"""REST API views for the tests of the apps below the reporting layer, which
have no app views of their own to call."""

from baseclasses.managers.montrek_manager import MontrekManager
from baseclasses.pages import MontrekPage
from baseclasses.views import (
    MontrekApiViewMixin,
    MontrekRestApiView,
    MontrekTemplateView,
)
from django.conf import settings
from django.urls import URLPattern, URLResolver, include, path


class ApiTestManager(MontrekManager):
    def to_json(self) -> list:
        return []


class ApiTestPage(MontrekPage):
    page_title = "API test"

    def get_tabs(self) -> tuple:
        return ()


class ApiTestPageView(MontrekApiViewMixin, MontrekTemplateView):
    """A page that answers REST requests as well, as a list view does."""

    manager_class = ApiTestManager
    page_class = ApiTestPage
    title = "API test page"

    def get_template_context(self) -> dict:
        return {}


class ApiTestRestView(MontrekRestApiView):
    manager_class = ApiTestManager


class ApiTestUrls:
    @staticmethod
    def urlpatterns() -> list[URLPattern | URLResolver]:
        """The test views next to the project URLs, for a test module that
        assigns them to its ``urlpatterns`` and sets ``ROOT_URLCONF`` to
        itself. Call it at import time, before the setting is overridden."""
        return [
            path("api-test/page/", ApiTestPageView.as_view(), name="api_test_page"),
            path("api-test/rest/", ApiTestRestView.as_view(), name="api_test_rest"),
            path("", include(settings.ROOT_URLCONF)),
        ]
