from django.contrib import admin
from .models import TransactionHub, TransactionSatellite

# Register your models here.
admin.site.register(TransactionHub)
admin.site.register(TransactionSatellite)
