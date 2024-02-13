from user.models import MontrekUser
from django import forms
from django.contrib.auth import forms as auth_forms


class MontrekAuthFormMixin:
    class Meta:
        model = MontrekUser
        fields = ("email",)
        field_classes = {"email": forms.EmailField}


class MontrekUserCreationForm(auth_forms.BaseUserCreationForm, MontrekAuthFormMixin):
    pass


class MontrekPasswordResetForm(auth_forms.PasswordResetForm, MontrekAuthFormMixin):
    pass


class MontrekUserChangeForm(auth_forms.UserChangeForm, MontrekAuthFormMixin):
    pass


class MontrekAuthenticationForm(auth_forms.AuthenticationForm, MontrekAuthFormMixin):
    pass

class MontrekPasswordChangeForm(auth_forms.PasswordChangeForm, MontrekAuthFormMixin):
    pass
