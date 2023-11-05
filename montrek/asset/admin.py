from django.contrib import admin
from .models import AssetHub
from .models import AssetStaticSatellite
from .models import AssetLiquidSatellite
from .models import AssetTimeSeriesSatellite

# Register your models here.

admin.site.register(AssetHub)
admin.site.register(AssetStaticSatellite)
admin.site.register(AssetLiquidSatellite)
admin.site.register(AssetTimeSeriesSatellite)
