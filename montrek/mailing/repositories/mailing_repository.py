from baseclasses.repositories.montrek_repository import MontrekRepository
from mailing.models import MailHub, MailSatellite


class MailingRepository(MontrekRepository):
    hub_class = MailHub

    def std_queryset(self):
        self.add_satellite_fields_annotations(
            MailSatellite,
            ["mail_subject", "mail_message", "mail_recipients", "mail_state"],
        )
        return self.build_queryset()
