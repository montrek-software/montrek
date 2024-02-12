from user.models import MontrekUser
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm

from django.contrib.auth.forms import (
    UserCreationForm,
    PasswordResetForm,
    UserChangeForm,
    AuthenticationForm,
)


class MontrekUserCreationForm(UserCreationForm):
    class Meta:
        model = MontrekUser
        fields = ("email",)


class MontrekPasswordResetForm(PasswordResetForm):
    class Meta:
        model = MontrekUser
        fields = ("email",)


class MontrekUserChangeForm(UserChangeForm):
    class Meta:
        model = MontrekUser
        fields = ("email",)


class MontrekAuthenticationForm(AuthenticationForm):
    class Meta:
        model = MontrekUser
        fields = ("email",)
