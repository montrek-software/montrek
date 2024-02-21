from django.contrib import admin
from .models import CompanyHub, CompanyTimeSeriesSatellite
from .models import CompanyStaticSatellite

admin.site.register(CompanyHub)
admin.site.register(CompanyStaticSatellite)
admin.site.register(CompanyTimeSeriesSatellite)
