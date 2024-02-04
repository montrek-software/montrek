from user.models import MontrekUser
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm


class MontrekUserCreationForm(UserCreationForm):

    class Meta:
        model = MontrekUser
        fields = UserCreationForm.Meta.fields


class MontrekPasswordResetForm(PasswordResetForm):
    pass
