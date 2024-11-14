import factory
from baseclasses.tests.factories.montrek_factory_schemas import MontrekSatelliteFactory


class MailHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "mailing.MailHub"


class MailSatelliteFactory(MontrekSatelliteFactory):
    class Meta:
        model = "mailing.MailSatellite"

    hub_entity = factory.SubFactory(MailHubFactory)
    mail_subject = factory.Sequence(lambda n: f"Mail {n}")
    mail_message = factory.Sequence(lambda n: f"Mail message {n}")
    mail_recipients = ",".join([str(factory.Faker("email")) for _ in range(3)])
