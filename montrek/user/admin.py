from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from user.forms.montrek_user_auth_forms import (
    MontrekUserChangeForm,
    MontrekUserCreationForm,
)

from user.models import MontrekUser


class MontrekUserAdmin(UserAdmin):
    model = MontrekUser
    add_form = MontrekUserCreationForm
    form = MontrekUserChangeForm
    list_display = (
        "email",
        "is_staff",
        "is_active",
    )
    list_filter = (
        "email",
        "is_staff",
        "is_active",
    )
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Permissions",
            {"fields": ("is_staff", "is_active", "groups", "user_permissions")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
    )
    search_fields = ("email",)
    ordering = ("email",)


admin.site.register(MontrekUser, MontrekUserAdmin)
