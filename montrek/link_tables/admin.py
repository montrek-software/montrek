from django.contrib import admin
from .models import AccountTransactionLink
from .models import AccountCreditInstitutionLink

# Register your models here.
admin.site.register(AccountTransactionLink)
admin.site.register(AccountCreditInstitutionLink)
