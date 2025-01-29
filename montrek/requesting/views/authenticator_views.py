from baseclasses.views import MontrekTemplateView
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse


class AuthenticatorUserPasswordView(MontrekTemplateView):
    template_name = "auth_user_password.html"
    success_url: str = ""

    def get_template_context(self) -> dict:
        return {"title": f"Authentification {self.title}"}

    def post(self, request, *args, **kwargs):
        user = request.POST.get("user")
        password = request.POST.get("password")

        if not user or not password:
            messages.error(self.request, "Invalid user or password")
            return self.get(request)

        return HttpResponseRedirect(reverse(self.success_url))
