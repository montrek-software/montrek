import re
from urllib.parse import parse_qs

from django.conf import settings
from django.http import HttpResponseRedirect


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.login_redirect = HttpResponseRedirect(settings.LOGIN_URL)

    def __call__(self, request):
        is_login_exempt = self.is_login_exempt_path(request) or self.is_rest_api(
            request
        )
        if not request.user.is_authenticated and not is_login_exempt:
            return self.login_redirect
        response = self.get_response(request)
        return response

    def is_rest_api(self, request) -> bool:
        query_params = parse_qs(request.META.get("QUERY_STRING", ""))
        return query_params.get("gen_rest_api") == ["true"]

    def is_login_exempt_path(self, request) -> bool:
        if request.path == "/":
            return True
        for pattern in settings.LOGIN_EXEMPT_PATHS:
            if re.match(pattern, request.path.lstrip("/")):
                return True
        return False
