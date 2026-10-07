from enum import Enum


class SftpPermissions(Enum):
    """Gate the sftp views: the connections carry reusable credentials."""

    CAN_VIEW = "Can view SFTP connections"
    CAN_CREATE = "Can create SFTP connections"
    CAN_UPDATE = "Can update SFTP connections"
    CAN_DELETE = "Can delete SFTP connections"

    def __init__(self, permission_name: str):
        self.app_label = "sftp"
        self.permission_name = permission_name
        self.codename = permission_name.lower().replace(" ", "_")
        self.namespaced_codename = f"{self.app_label}.{self.codename}"
        self.model = "model independent"


class SftpUserGroups(Enum):
    VIEWER = ("SFTP Viewer", [SftpPermissions.CAN_VIEW])
    ADMIN = ("SFTP Admin", list(SftpPermissions))

    def __init__(self, group_name, permissions):
        self.group_name = group_name
        self.permissions = permissions
