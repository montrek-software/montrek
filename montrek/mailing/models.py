from django.db import models
from baseclasses import models as baseclass_models

# Create your models here.


class MailHub(baseclass_models.MontrekHubABC):
    pass


class MailSatellite(baseclass_models.MontrekSatelliteABC):
    class MailStates(models.TextChoices):
        PENDING = "Pending"
        SENT = "Sent"

    mail_subject = models.CharField(max_length=255)
    mail_message = models.TextField()
    mail_recipients = models.TextField()
    mail_state = models.CharField(
        max_length=10, choices=MailStates.choices, default=MailStates.PENDING
    )
    hub_entity = models.ForeignKey(MailHub, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Mail Satellite"
        verbose_name_plural = "Mail Satellites"

    identifier_fields = ["hub_entity_id"]
