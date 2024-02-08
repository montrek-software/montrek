from django.contrib import admin
from .models import CountryHub
from .models import CountryStaticSatellite

admin.site.register(CountryHub)
admin.site.register(CountryStaticSatellite)
