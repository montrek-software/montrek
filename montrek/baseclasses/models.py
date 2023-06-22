import datetime
from django.db import models
from django.utils import timezone

# Create your models here.

#Base Hub Model ABC
class MontrekHubABC(models.Model):
    class Meta:
        abstract = True

    identifier = models.CharField(max_length=12)


#Base Static Satellite Model ABC
class MontrekSatelliteABC(models.Model):
    class Meta:
        abstract = True
    state_date = models.DateTimeField(default=timezone.now)
    hub_entity = models.ForeignKey(MontrekHubABC, on_delete=models.CASCADE)

#Base Link Model ABC
class MontrekLinkABC(models.Model):
    class Meta:
        abstract = True
    from_hub = models.ForeignKey(MontrekHubABC, on_delete=models.CASCADE, related_name='from_hub')
    to_hub = models.ForeignKey(MontrekHubABC, on_delete=models.CASCADE, related_name='to_hub')


class TestMontrekHub(MontrekHubABC):
    pass

class TestMontrekSatellite(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(TestMontrekHub, on_delete=models.CASCADE)
    test_name = models.CharField(max_length=12)

class TestMontrekLink(MontrekLinkABC):
    from_hub = models.ForeignKey(TestMontrekHub, on_delete=models.CASCADE, related_name='from_hub')
    to_hub = models.ForeignKey(TestMontrekHub, on_delete=models.CASCADE, related_name='to_hub')
