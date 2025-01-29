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

        self.session_data["user"] = user[0]
        self.session_data["password"] = password[0]
        self.process_authenticator()

        return HttpResponseRedirect(reverse(self.success_url))

    def process_authenticator(self):
        raise NotImplementedError("process_authenticator must be implemented")
