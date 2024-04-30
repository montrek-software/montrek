from django.shortcuts import redirect
from django.urls import reverse
from django.core.exceptions import PermissionDenied


class PermissionErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, PermissionDenied):
            # Redirect to the login page
            return redirect(reverse("login"))
