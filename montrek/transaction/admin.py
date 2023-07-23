from django.contrib import admin
from .models import TransactionHub, TransactionSatellite
from .models import TransactionTypeHub, TransactionTypeSatellite

# Register your models here.
admin.site.register(TransactionHub)
admin.site.register(TransactionSatellite)
admin.site.register(TransactionTypeHub)
admin.site.register(TransactionTypeSatellite)
