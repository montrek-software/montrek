from django.contrib import admin
from .models import CreditInstitutionStaticSatellite
from .models import CreditInstitutionHub

# Register your models here
admin.site.register(CreditInstitutionStaticSatellite)
admin.site.register(CreditInstitutionHub)
