from django.conf import settings
from django.contrib import messages
from baseclasses.forms import LocalizedText
from baseclasses.utils import get_safe_redirect_url, htmx_aware_redirect
from django.urls import reverse
from django.core.exceptions import PermissionDenied

MISSING_PERMISSION_TEXT = LocalizedText(
    en="You do not have the required permissions to access this page.",
    de="Sie haben nicht die erforderlichen Berechtigungen, um auf diese Seite zuzugreifen.",
)


def get_missing_permission_message() -> str:
    """The missing-permission message in the language set via LANGUAGE_CODE.

    Resolved per call rather than at import time, so a settings override (tests,
    a settings reload) sees the language currently configured.
    """
    return str(MISSING_PERMISSION_TEXT)


class PermissionErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, PermissionDenied):
            messages.error(
                request,
                get_missing_permission_message(),
            )
            if request.user.is_authenticated:
                redirect_url = get_safe_redirect_url(
                    request, request.META.get("HTTP_REFERER"), reverse("home")
                )
            else:
                redirect_url = settings.LOGIN_URL
            # htmx aware: a denied action is usually clicked on an hx-post
            # button, and a plain redirect would be swapped into that button.
            return htmx_aware_redirect(request, redirect_url)
        return None
