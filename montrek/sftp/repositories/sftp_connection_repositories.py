from baseclasses.repositories.montrek_repository import MontrekRepository
from sftp.models.sftp_connection_hub_models import SftpConnectionHub


class SftpConnectionRepository(MontrekRepository):
    hub_class = SftpConnectionHub

    def set_annotations(self):
        pass
