from django import forms
from django.contrib.auth import forms as auth_forms, get_user_model


class MontrekUserCreationForm(auth_forms.BaseUserCreationForm):
    class Meta(auth_forms.BaseUserCreationForm.Meta):
        model = get_user_model()
        fields = ("email",)
        field_classes = {"email": forms.EmailField}


class MontrekPasswordResetForm(auth_forms.PasswordResetForm):
    def clean_email(self):
        """
        Validates that an active user exists with the given email address.
        """
        email = self.cleaned_data["email"]
        user = get_user_model().objects.filter(email__iexact=email, is_active=True)
        if not user:
            raise forms.ValidationError(
                "This email address doesn't have an associated user account."
            )
        return email


class MontrekUserChangeForm(auth_forms.UserChangeForm):
    pass


class MontrekAuthenticationForm(auth_forms.AuthenticationForm):
    pass


class MontrekPasswordChangeForm(auth_forms.PasswordChangeForm):
    pass
