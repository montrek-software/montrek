from baseclasses.access import AccessKind, AccessPolicy
from baseclasses.app_config import MontrekAppConfig

from sftp.user_groups.constants import SftpPermissions


class SftpConfig(MontrekAppConfig):
    # Django skips an app config that inherits 'default = False' from
    # MontrekAppConfig, so this has to be declared here.
    default = True
    name = "sftp"
    # The connections carry reusable credentials, so no view is open to everybody
    access_policy = AccessPolicy.RESTRICTED
    access_permissions = {
        AccessKind.VIEW: SftpPermissions.CAN_VIEW,
        AccessKind.CREATE: SftpPermissions.CAN_CREATE,
        AccessKind.UPDATE: SftpPermissions.CAN_UPDATE,
        AccessKind.DELETE: SftpPermissions.CAN_DELETE,
    }
