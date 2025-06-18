from urllib.parse import urlencode
from django.contrib.auth import login, logout
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views
from django.views import View, generic as generic_views
from django.contrib import messages
from user import forms

KEYCLOAK_URL = "http://localhost:8080/realms/montrek"


class MessageHandlerMixin:
    def add_form_error_messages(self, form):
        for field, errors in form.errors.items():
            field = field.replace("_", "").capitalize()
            for error in errors:
                messages.error(self.request, f"{field}: {error}")

    def add_successfull_login_message(self, email):
        messages.info(self.request, f"You have logged in as {email}!")


class MontrekSignUpView(generic_views.CreateView, MessageHandlerMixin):
    form_class = forms.MontrekUserCreationForm
    template_name = "user/user_base.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        login(self.request, user)
        self.add_successfull_login_message(user.email)
        return response

    def form_invalid(self, form):
        self.add_form_error_messages(form)
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Sign Up"
        return context


class MontrekLoginView(generic_views.FormView, MessageHandlerMixin):
    def get(self, request, *args, **kwargs):
        return redirect("oidc_authentication_init")


class MontrekLogoutView(View):
    def dispatch(self, request, *args, **kwargs):
        logout(request)
        keycloak_logout_url = KEYCLOAK_URL + "/protocol/openid-connect/logout"
        return redirect(keycloak_logout_url)


class MontrekPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "user/user_base.html"


class MontrekPasswordResetView(auth_views.PasswordResetView, MessageHandlerMixin):
    form_class = forms.MontrekPasswordResetForm
    template_name = "user/user_base.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        messages.info(
            self.request,
            "We've emailed you instructions for setting your password. You should receive the email shortly!",
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        self.add_form_error_messages(form)
        return super().form_invalid(form)


class MontrekPasswordResetCompleteView(generic_views.RedirectView):
    url = reverse_lazy("login")

    def get(self, request, *args, **kwargs):
        messages.info(
            request, "Your password has been set. You may go ahead and login."
        )
        return super().get(request, *args, **kwargs)


class MontrekPasswordChangeView(auth_views.PasswordChangeView, MessageHandlerMixin):
    form_class = forms.MontrekPasswordChangeForm
    template_name = "user/user_base.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        messages.info(self.request, "Your password has been changed.")
        return super().form_valid(form)

    def form_invalid(self, form):
        self.add_form_error_messages(form)
        return super().form_invalid(form)
