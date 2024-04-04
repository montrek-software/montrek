from django.contrib.auth import login
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http.response import HttpResponseRedirect
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views
from django.views import generic as generic_views
from django.contrib import messages
from user import forms


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


class MontrekLogoutView(auth_views.LogoutView):
    pass


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
