from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, FormView


class SignUpView(CreateView):
    form_class = UserCreationForm
    template_name = 'user/signup.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        login(self.request, self.object)
        return super().form_valid(form)


class LoginView(FormView):
    form_class = AuthenticationForm
    template_name = 'user/login.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        login(self.request, form.get_user())
        return super().form_valid(form)
