from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from user.models import MontrekUser

class MontrekUserAdmin(UserAdmin):
    model = MontrekUser

admin.site.register(MontrekUser, MontrekUserAdmin)
