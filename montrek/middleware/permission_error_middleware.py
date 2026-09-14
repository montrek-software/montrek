from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from baseclasses.utils import get_safe_redirect_url
from django.urls import reverse
from django.core.exceptions import PermissionDenied

MISSING_PERMISSION_MESSAGE = (
    "You do not have the required permissions to access this page."
)


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
                MISSING_PERMISSION_MESSAGE,
            )
            if request.user.is_authenticated:
                redirect_url = get_safe_redirect_url(
                    request, request.META.get("HTTP_REFERER"), reverse("home")
                )
            else:
                redirect_url = settings.LOGIN_URL
            return HttpResponseRedirect(redirect_url)
        return None
