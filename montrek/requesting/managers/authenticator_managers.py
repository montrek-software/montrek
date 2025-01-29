from base64 import b64encode
from typing import Any
from abc import ABC, abstractmethod
from baseclasses.managers.montrek_manager import MontrekManager


class RequestAuthenticator(MontrekManager):
    def __init__(self, session_data: dict[str, Any]):
        super().__init__(session_data)
        self.credentials = self.get_credentials()

    @abstractmethod
    def get_credentials(self) -> dict:
        ...

    @abstractmethod
    def get_headers(self):
        return {}


class RequestUserPasswordAuthenticator(RequestAuthenticator):
    def get_credentials(self):
        return {
            "user": self.session_data["user"],
            "password": self.session_data["password"],
        }

    def get_headers(self):
        credentials = b64encode(
            f"{self.credentials["user"]}:{self.credentials["password"]}".encode()
        ).decode()
        return {"Authorization": f"Basic {credentials}"}


class RequestBearerAuthenticator(RequestAuthenticator):
    def get_credentials(self):
        return {"token": self.session_data["token"]}

    def get_headers(self):
        return {"Authorization": f"Bearer {self.credentials["token"]}"}


class RequestSlugAuthenticator(RequestAuthenticator):
    def get_credentials(self):
        return {"slug": self.session_data["slug"], "token": self.session_data["token"]}

    def get_headers(self):
        return {
            "Authorization": f"{self.credentials["slug"]}:{self.credentials["token"]}"
        }
