from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.conf import settings


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.login_redirect = HttpResponseRedirect(reverse_lazy("login"))

    def __call__(self, request):
        is_login_exempt = request.path.startswith(tuple(settings.LOGIN_EXEMPT_PATHS))
        if not request.user.is_authenticated and not is_login_exempt:
            return self.login_redirect
        response = self.get_response(request)
        return response
