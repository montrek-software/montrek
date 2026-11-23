"""The default storage, as STORAGE_BACKEND configures it.

A class of its own rather than code in settings.py, which runs only once per
process: the tests call it with a config of their own.
"""

from typing import Any

from decouple import Config
from django.core.exceptions import ImproperlyConfigured

BACKENDS = ("filesystem", "azure")


class StorageSettings:
    def __init__(self, config: Config) -> None:
        self.config = config

    def default_storage(self) -> dict[str, Any]:
        """The STORAGES["default"] entry: where uploads, exports and other
        stored files go."""
        backend = self.config("STORAGE_BACKEND", default="filesystem")
        if backend == "filesystem":
            return {"BACKEND": "django.core.files.storage.FileSystemStorage"}
        if backend == "azure":
            return self.azure_storage()
        raise ImproperlyConfigured(
            f"STORAGE_BACKEND must be one of {', '.join(BACKENDS)}, not {backend!r}."
        )

    def azure_storage(self) -> dict[str, Any]:
        """A private Blob Storage container, for a platform without a shared
        disk."""
        account_name = self.config("AZURE_STORAGE_ACCOUNT_NAME", default="")
        if not account_name:
            raise ImproperlyConfigured(
                "STORAGE_BACKEND=azure needs AZURE_STORAGE_ACCOUNT_NAME."
            )
        # Every url() is a SAS valid this long. 0 would make the backend hand
        # out the bare blob URL, and a negative value an expired SAS; a private
        # container refuses both, so downloads fail while uploads still work.
        expiration_secs = self.config(
            "AZURE_STORAGE_URL_EXPIRATION_SECS", default=300, cast=int
        )
        if expiration_secs <= 0:
            raise ImproperlyConfigured(
                "AZURE_STORAGE_URL_EXPIRATION_SECS must be a positive number of "
                f"seconds, not {expiration_secs}."
            )
        options: dict[str, Any] = {
            "account_name": account_name,
            "azure_container": self.config(
                "AZURE_STORAGE_CONTAINER", default="uploads"
            ),
            "expiration_secs": expiration_secs,
        }
        connection_string = self.config("AZURE_STORAGE_CONNECTION_STRING", default="")
        if connection_string:
            # Another endpoint, such as Azurite. URLs are still signed with the
            # account key, so that is needed as well.
            options["connection_string"] = connection_string
        account_key = self.config("AZURE_STORAGE_ACCOUNT_KEY", default="")
        if account_key:
            options["account_key"] = account_key
        else:
            # No key: sign in as the container app's managed identity
            # (AZURE_CLIENT_ID picks a user-assigned one), and sign URLs with a
            # user delegation key. Imported here: only an Azure install needs
            # azure-identity loaded.
            from azure.identity import DefaultAzureCredential

            options["token_credential"] = DefaultAzureCredential()
        return {
            "BACKEND": "storages.backends.azure_storage.AzureStorage",
            "OPTIONS": options,
        }
