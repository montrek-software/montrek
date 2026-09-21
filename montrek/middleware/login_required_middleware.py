import re
from urllib.parse import parse_qs

from django.conf import settings

from baseclasses.utils import htmx_aware_redirect


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
        query_params = parse_qs(request.META.get("QUERY_STRING", ""))
        return query_params.get("gen_rest_api") == ["true"]

    def is_login_exempt_path(self, request) -> bool:
        # Exempt the root path ('/') because it is handled separately (presumably by URL routing)
        # to redirect to '/home'.
        if request.path == "/":
            return True
        for pattern in settings.LOGIN_EXEMPT_PATHS:
            if re.match(pattern, request.path.lstrip("/")):
                return True
        return False
