from django.contrib import admin
from .models import CurrencyHub
from .models import CurrencyStaticSatellite
from .models import CurrencyTimeSeriesSatellite

# Register your models here.

admin.site.register(CurrencyHub)
admin.site.register(CurrencyStaticSatellite)
admin.site.register(CurrencyTimeSeriesSatellite)
