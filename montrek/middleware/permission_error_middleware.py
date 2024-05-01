from django.contrib import messages
from django.http import HttpResponseRedirect
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
            messages.error(request, "You do not have permission to access this page.")
            if request.user.is_authenticated:
                redirect_url = request.META.get("HTTP_REFERER") or reverse("home")
            else:
                redirect_url = reverse("login")
            return HttpResponseRedirect(redirect_url)
