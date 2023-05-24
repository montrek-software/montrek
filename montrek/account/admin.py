from django.contrib import admin
from .models import AccountHub
from .models import AccountStaticSatellite
from .models import BankAccountSatellite

# Register your models here.
admin.site.register(AccountHub)
admin.site.register(AccountStaticSatellite)
admin.site.register(BankAccountSatellite)
