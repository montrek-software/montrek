from baseclasses.repositories.montrek_repository import MontrekRepository
from mailing.models import MailHub, MailSatellite, MailStateSatellite


class MailingRepository(MontrekRepository):
    hub_class = MailHub

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            MailSatellite,
            ["mail_recipients", "mail_subject", "mail_message", "mail_attachments"],
        )
        self.add_satellite_fields_annotations(
            MailStateSatellite, ["mail_state", "mail_comment"]
        )
