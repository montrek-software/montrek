from baseclasses.managers.montrek_manager import MontrekManager
from mailing.repositories.mailing_repository import MailingRepository


class MailingManager(MontrekManager):
    repository_class = MailingRepository
