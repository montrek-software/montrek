from django.contrib import admin
from montrek_example import models as me_models

# Register your models here.
admin.site.register(me_models.HubB)
admin.site.register(me_models.SatB1)
admin.site.register(me_models.SatB2)
admin.site.register(me_models.HubA)
admin.site.register(me_models.SatA1)
admin.site.register(me_models.SatA2)
admin.site.register(me_models.LinkHubAHubB)
admin.site.register(me_models.HubD)
admin.site.register(me_models.SatD1)
