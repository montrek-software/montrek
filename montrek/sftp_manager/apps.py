from baseclasses.access import AccessPolicy
from baseclasses.app_config import MontrekAppConfig


class SftpManagerConfig(MontrekAppConfig):
    # Django skips an app config that inherits 'default = False' from
    # MontrekAppConfig, so this has to be declared here.
    default = True
    name = "sftp_manager"
    access_policy = AccessPolicy.OPEN
