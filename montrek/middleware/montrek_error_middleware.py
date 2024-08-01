from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse

from baseclasses.errors.montrek_user_error import MontrekError


class MontrekErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, MontrekError):
            msg = exception.args[0]
            messages.error(
                request,
                msg,
            )
            redirect_url = request.META.get("HTTP_REFERER") or reverse("home")
            return HttpResponseRedirect(redirect_url)
