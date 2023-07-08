import datetime
import hashlib
from django.db import models
from django.utils import timezone

# Create your models here.

class TimeStampMixin(models.Model):
    class Meta:
        abstract = True
    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now=True )

#Base Hub Model ABC
class MontrekHubABC(TimeStampMixin):
    class Meta:
        abstract = True

    identifier = models.CharField(max_length=12, default='')


#Base Static Satellite Model ABC
class MontrekSatelliteABC(TimeStampMixin):
    class Meta:
        abstract = True
    state_date = models.DateTimeField(default=timezone.now)
    hub_entity = models.ForeignKey(MontrekHubABC, on_delete=models.CASCADE)
    hash_identifier = models.CharField(max_length=64, default='')

    def save(self, *args, **kwargs):
        self._get_identifier_hash()
        super().save(*args, **kwargs)

    def _get_identifier_hash(self) -> None:
        if not hasattr(self, 'identifier_fields'):
            raise AttributeError(f'Satellite {self.__class__.__name__} must have attribute identifier_fields')
        identifier_string = ''.join(str(getattr(self, field)) for field in self.identifier_fields)
        sha256_hash = hashlib.sha256(identifier_string.encode()).hexdigest()
        self.hash_identifier = sha256_hash

#Base Link Model ABC
class MontrekLinkABC(TimeStampMixin):
    class Meta:
        abstract = True
    from_hub = models.ForeignKey(MontrekHubABC, on_delete=models.CASCADE, related_name='from_hub')
    to_hub = models.ForeignKey(MontrekHubABC, on_delete=models.CASCADE, related_name='to_hub')


class TestMontrekHub(MontrekHubABC):
    pass

class TestMontrekSatellite(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(TestMontrekHub, on_delete=models.CASCADE)
    identifier_fields = ['test_name']
    test_name = models.CharField(max_length=12)

class TestMontrekSatelliteNoIdFields(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(TestMontrekHub, on_delete=models.CASCADE)

class TestMontrekLink(MontrekLinkABC):
    from_hub = models.ForeignKey(TestMontrekHub, on_delete=models.CASCADE, related_name='from_hub')
    to_hub = models.ForeignKey(TestMontrekHub, on_delete=models.CASCADE, related_name='to_hub')
