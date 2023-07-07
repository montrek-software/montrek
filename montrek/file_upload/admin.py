from django.contrib import admin
from .models import FileUploadFileHub
from .models import FileUploadFileStaticSatellite
from .models import FileUploadRegistryHub
from .models import FileUploadRegistryStaticSatellite
# Register your models here.

admin.site.register(FileUploadFileHub)
admin.site.register(FileUploadFileStaticSatellite)
admin.site.register(FileUploadRegistryHub)
admin.site.register(FileUploadRegistryStaticSatellite)
