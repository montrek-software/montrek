from django.contrib import admin
from .models import TransactionHub, TransactionSatellite
from .models import TransactionTypeHub, TransactionTypeSatellite
from .models import TransactionCategoryHub, TransactionCategorySatellite
from .models import TransactionCategoryMapHub, TransactionCategoryMapSatellite

# Register your models here.
admin.site.register(TransactionHub)
admin.site.register(TransactionSatellite)
admin.site.register(TransactionTypeHub)
admin.site.register(TransactionTypeSatellite)
admin.site.register(TransactionCategoryHub)
admin.site.register(TransactionCategorySatellite)
admin.site.register(TransactionCategoryMapHub)
admin.site.register(TransactionCategoryMapSatellite)
