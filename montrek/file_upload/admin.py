from django.contrib import admin
from .models import FieldMapHub, FieldMapStaticSatellite, FileUploadFileHub
from .models import FileUploadFileStaticSatellite

# Register your models here.

admin.site.register(FileUploadFileHub)
admin.site.register(FileUploadFileStaticSatellite)
admin.site.register(FieldMapHub)
admin.site.register(FieldMapStaticSatellite)
