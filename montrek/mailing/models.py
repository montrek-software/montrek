from django.db import models
from baseclasses import models as baseclass_models
from baseclasses.fields import HubForeignKey

# Create your models here.


class MailHub(baseclass_models.MontrekHubABC):
    pass


class MailHubValueDate(baseclass_models.HubValueDate):
    hub = HubForeignKey(MailHub)


class MailSatellite(baseclass_models.MontrekSatelliteABC):
    hub_entity = models.ForeignKey(MailHub, on_delete=models.CASCADE)
    mail_subject = models.CharField(max_length=255)
    mail_message = models.TextField()
    mail_recipients = models.TextField()
    mail_attachments = models.TextField(default="", blank=True, null=True)
    mail_bcc = models.TextField(default="", blank=True, null=True)

    class Meta:
        verbose_name = "Mail Satellite"
        verbose_name_plural = "Mail Satellites"

    identifier_fields = ["hub_entity_id"]


class MailStateSatellite(baseclass_models.MontrekSatelliteABC):
    hub_entity = models.ForeignKey(MailHub, on_delete=models.CASCADE)

    class MailStates(models.TextChoices):
        PENDING = "Pending"
        SENT = "Sent"

    mail_state = models.CharField(
        max_length=10, choices=MailStates.choices, default=MailStates.PENDING
    )
    mail_comment = models.TextField(null=True, blank=True)
    identifier_fields = ["hub_entity_id"]
