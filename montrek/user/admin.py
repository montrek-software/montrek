from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from user.forms import MontrekUserChangeForm, MontrekUserCreationForm

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
            {
                "fields": ("is_staff", "is_active", "groups", "user_permissions"),
                "description": (
                    "Users are not deleted, so the history keeps who created "
                    "what. To stop a user from signing in, untick Active."
                ),
            },
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

    def has_delete_permission(self, request, obj=None):
        # What a user created refers to them (created_by, on_delete=RESTRICT):
        # they are deactivated instead, for every admin, superusers included.
        return False


admin.site.register(MontrekUser, MontrekUserAdmin)
