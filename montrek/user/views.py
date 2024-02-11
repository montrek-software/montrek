from django.contrib.auth import login
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, FormView
from django.contrib import messages
from user.forms import MontrekPasswordResetForm, MontrekUserCreationForm
from user.forms import MontrekAuthenticationForm

class MessageHandlerMixin:
    def add_form_error_messages(self, form):
        for field, errors in form.errors.items():
            field = field.replace("_", "").capitalize()
            for error in errors:
                messages.error(self.request, f"{field}: {error}")

    def add_successfull_login_message(self, email):
        messages.info(self.request, f"You have logged in as {email}!")


class SignUpView(CreateView, MessageHandlerMixin):
    form_class = MontrekUserCreationForm
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


class LoginView(FormView, MessageHandlerMixin):
    form_class = MontrekAuthenticationForm
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


class PasswordResetView(FormView, MessageHandlerMixin):
    form_class = MontrekPasswordResetForm
    template_name = "user/user_base.html"

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        self.add_successfull_login_message(user.username)
        return super().form_valid(form)

    def form_invalid(self, form):
        self.add_form_error_messages(form)
        return super().form_invalid(form)
