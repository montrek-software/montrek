from django import forms
from django.contrib.auth import forms as auth_forms, get_user_model


class MontrekUserCreationForm(auth_forms.BaseUserCreationForm):

    class Meta(auth_forms.BaseUserCreationForm.Meta):
        model = get_user_model()
        fields = ("email",)
        field_classes = {"email": forms.EmailField}


class MontrekPasswordResetForm(auth_forms.PasswordResetForm):
    pass

class MontrekUserChangeForm(auth_forms.UserChangeForm):
    pass

class MontrekAuthenticationForm(auth_forms.AuthenticationForm):
    pass

class MontrekPasswordChangeForm(auth_forms.PasswordChangeForm):
    pass
