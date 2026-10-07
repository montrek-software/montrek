from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from reporting.managers.montrek_details_manager import MontrekDetailsManager
from sftp.repositories.sftp_connection_repositories import SftpConnectionRepository


class CommonTableElementsMixin:
    @property
    def table_elements(self):
        return [
            te.StringTableElement(name="Host", attr="host"),
            te.IntTableElement(name="Port", attr="port"),
            te.StringTableElement(name="User", attr="user"),
            te.StringTableElement(name="Base Path", attr="base_path"),
            te.StringTableElement(name="Auth Method", attr="auth_method"),
            te.LinkTableElement(
                name="Edit",
                url="sftp_connection_update",
                icon="edit",
                kwargs={"pk": "id"},
                hover_text="Update Sftp Connection",
            ),
            te.LinkTableElement(
                name="Delete",
                url="sftp_connection_delete",
                icon="trash",
                kwargs={"pk": "id"},
                hover_text="Delete Sftp Connection",
            ),
        ]


class SftpConnectionTableManager(CommonTableElementsMixin, MontrekTableManager):
    repository_class = SftpConnectionRepository

    @property
    def table_elements(self):
        table_elements = [
            te.LinkTextTableElement(
                name="Details",
                url="sftp_connection_details",
                kwargs={"pk": "hub_id"},
                text="hub_entity_id",
                hover_text="View Sftp Connection Details",
            ),
        ]
        table_elements += super().table_elements
        return table_elements


class SftpConnectionDetailsManager(CommonTableElementsMixin, MontrekDetailsManager):
    repository_class = SftpConnectionRepository

    @property
    def table_elements(self):
        table_elements = [
            te.StringTableElement(name="hub", attr="hub_entity_id"),
        ]
        table_elements += super().table_elements
        # Secrets are annotated onto the hub value date, where the table element
        # cannot detect the encrypted model field, so they are masked explicitly.
        table_elements += [
            te.StringTableElement(
                name="Host Key Fingerprint", attr="host_key_fingerprint"
            ),
            te.BooleanTableElement(name="Trusted Host", attr="trusted_host"),
            te.IntTableElement(name="Timeout (s)", attr="timeout_seconds"),
            te.SecretStringTableElement(name="Password", attr="password"),
            te.SecretStringTableElement(name="Private Key", attr="private_key"),
            te.SecretStringTableElement(
                name="Private Key Passphrase", attr="private_key_passphrase"
            ),
        ]
        return table_elements
