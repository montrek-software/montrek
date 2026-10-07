from baseclasses.access import AccessPolicy
from baseclasses.app_config import MontrekAppConfig


class SftpConfig(MontrekAppConfig):
    # Django skips an app config that inherits 'default = False' from
    # MontrekAppConfig, so this has to be declared here.
    default = True
    name = "sftp"
    access_policy = AccessPolicy.OPEN
