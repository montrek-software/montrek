import re

from django.conf import settings
from django.urls import Resolver404, resolve

from baseclasses.utils import htmx_aware_redirect
from baseclasses.views import MontrekApiViewMixin


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        is_login_exempt = self.is_login_exempt_path(request) or self.is_rest_api(
            request
        )
        if not request.user.is_authenticated and not is_login_exempt:
            # Built per request rather than once in __init__: a single response
            # instance shared by every request is mutable state, and the answer
            # now depends on the request anyway - a session that expired while
            # the page was open is most likely noticed by an htmx call, which
            # would otherwise swap the login page into whatever was clicked.
            return htmx_aware_redirect(request, settings.LOGIN_URL)
        return self.get_response(request)

    def is_rest_api(self, request) -> bool:
        # A REST request to an API view is left to the view: it checks the
        # bearer token itself (MontrekApiViewMixin). Anything else, including
        # ?gen_rest_api=true on a page that is no API view, needs the login.
        try:
            match = resolve(request.path_info)
        except Resolver404:
            return False
        view_class = getattr(match.func, "view_class", None)
        return (
            isinstance(view_class, type)
            and issubclass(view_class, MontrekApiViewMixin)
            and view_class.is_rest_request(request)
        )

    def is_login_exempt_path(self, request) -> bool:
        return is_login_exempt_path(request.path)


def is_login_exempt_path(path: str) -> bool:
    # Exempt the root path ('/') because it is handled separately (presumably by URL routing)
    # to redirect to '/home'.
    if path == "/":
        return True
    return any(
        re.match(pattern, path.lstrip("/")) for pattern in settings.LOGIN_EXEMPT_PATHS
    )
