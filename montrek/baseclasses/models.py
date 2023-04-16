import datetime
from django.db import models

# Create your models here.

#Base Hub Model ABC
class MontrekHubABC(models.Model):
    class Meta:
        abstract = True

    identifier = models.CharField(max_length=12)


#Base Satellite Model ABC
class MontrekSatelliteABC(models.Model):
    class Meta:
        abstract = True
    start_date = models.DateTimeField(default=datetime.datetime.now())
    end_date = models.DateTimeField(default=datetime.datetime(2100,1,1))
    hub_entity = models.ForeignKey(MontrekHubABC, on_delete=models.CASCADE)

#Base Link Model ABC
class MontrekLinkABC(models.Model):
    class Meta:
        abstract = True

