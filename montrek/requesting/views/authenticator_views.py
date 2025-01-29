from django.http import HttpResponseRedirect
from django.urls import reverse
from baseclasses.views import MontrekTemplateView


class AuthenticatorUserPasswordView(MontrekTemplateView):
    template_name = "auth_user_password.html"
    success_url: str = ""

    def get_template_context(self) -> dict:
        return {"title": f"Authentification {self.title}"}

    def post(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse(self.success_url))
