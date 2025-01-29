from baseclasses.views import MontrekTemplateView


class AuthenticatorUserPasswordView(MontrekTemplateView):
    template_name = "auth_user_password.html"

    def get_template_context(self) -> dict:
        return {"title": f"Authentification {self.title}"}

    # def post(self, request, *args, **kwargs):
    #     breakpoint()
