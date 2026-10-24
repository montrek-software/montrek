from typing import cast

from django.contrib.auth import login, logout
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.views import redirect_to_login
from django.http import Http404, HttpResponseNotAllowed
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_http_methods
from django.contrib.auth import views as auth_views
from django.views import generic as generic_views
from django.contrib import messages
from mozilla_django_oidc.views import OIDCAuthenticationRequestView
from user import forms
from user.modules.oidc_provider import OidcProvider


class MessageHandlerMixin:
    def add_form_error_messages(self, form):
        for field, errors in form.errors.items():
            field = field.replace("_", "").capitalize()
            for error in errors:
                messages.error(self.request, f"{field}: {error}")

    def add_successfull_login_message(self, email):
        messages.info(self.request, f"You have logged in as {email}!")


class PasswordLoginMixin:
    """For the views that sign in, or set a password, with the Django password:
    not there when OIDC handles the sign-in (settings.ALLOW_PASSWORD_LOGIN)."""

    def dispatch(self, request, *args, **kwargs):
        if not settings.ALLOW_PASSWORD_LOGIN:
            raise Http404
        return super().dispatch(request, *args, **kwargs)


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

    def dispatch(self, request, *args, **kwargs):
        if not settings.ALLOW_SIGNUP:
            raise Http404
        return super().dispatch(request, *args, **kwargs)


class MontrekLoginView(generic_views.FormView, MessageHandlerMixin):
    form_class = forms.MontrekAuthenticationForm
    template_name = "user/user_base.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        self.add_successfull_login_message(user.email)
        return super().form_valid(form)

    def form_invalid(self, form):
        self.add_form_error_messages(form)
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Login"
        context["link_text"] = "Lost password?"
        context["link"] = reverse_lazy("password_reset")
        return context

    def get(self, request, *args, **kwargs):
        if settings.ENABLE_OIDC:
            return redirect("oidc_authentication_init")
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not settings.ALLOW_PASSWORD_LOGIN:
            return HttpResponseNotAllowed(["GET"])
        return super().post(request, *args, **kwargs)


@require_http_methods(["GET", "POST"])
def admin_login(request, extra_context=None):
    """Django's admin login, or the provider's when the password is not
    accepted. A user who is signed in but no staff member gets the admin's own
    page, which says so, rather than being sent round to the provider again.
    The admin's login view protects its form against CSRF."""
    if request.method == "POST" and not settings.ALLOW_PASSWORD_LOGIN:
        return HttpResponseNotAllowed(["GET"])
    if settings.ALLOW_PASSWORD_LOGIN or request.user.is_authenticated:
        return admin.site.login(request, extra_context)
    return redirect_to_login(
        request.GET.get("next") or reverse("admin:index"), settings.LOGIN_URL
    )


class MontrekOIDCAuthenticationRequestView(OIDCAuthenticationRequestView):
    get_settings = staticmethod(OidcProvider.get_settings)


class MontrekLogoutView(auth_views.LogoutView):
    def dispatch(self, request, *args, **kwargs):
        if settings.ENABLE_OIDC:
            logout_url = OidcProvider.logout_url()
            logout(request)
            # Without the provider's logout page its session stays open, and
            # the login page would sign the user straight back in.
            return redirect(logout_url or "logged_out")
        return super().dispatch(request, *args, **kwargs)


class MontrekLoggedOutView(generic_views.TemplateView):
    template_name = "user/logged_out.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Logged out"
        return context


class MontrekPasswordResetConfirmView(
    PasswordLoginMixin, auth_views.PasswordResetConfirmView
):
    template_name = "user/user_base.html"


class MontrekPasswordResetView(
    PasswordLoginMixin, auth_views.PasswordResetView, MessageHandlerMixin
):
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


class MontrekPasswordResetCompleteView(PasswordLoginMixin, generic_views.RedirectView):
    # The lazy string resolves on first use, like a str.
    url = cast(str, reverse_lazy("login"))

    def get(self, request, *args, **kwargs):
        messages.info(
            request, "Your password has been set. You may go ahead and login."
        )
        return super().get(request, *args, **kwargs)


class MontrekPasswordChangeView(
    PasswordLoginMixin, auth_views.PasswordChangeView, MessageHandlerMixin
):
    form_class = forms.MontrekPasswordChangeForm
    template_name = "user/user_base.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        messages.info(self.request, "Your password has been changed.")
        return super().form_valid(form)

    def form_invalid(self, form):
        self.add_form_error_messages(form)
        return super().form_invalid(form)
