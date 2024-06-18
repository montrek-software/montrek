from abc import abstractmethod
import requests
import pandas as pd
from base64 import b64encode

from baseclasses.managers.montrek_manager import MontrekManager


class RequestAuthenticator:
    def get_headers(self):
        return {}


class RequestUserPasswordAuthenticator:
    def __init__(self, user: str, password: str):
        self.user = user
        self.password = password

    def get_headers(self):
        credentials = b64encode(f"{self.user}:{self.password}".encode()).decode()
        return {"Authorization": f"Basic {credentials}"}


class RequestBearerAuthenticator:
    def __init__(self, token: str):
        self.token = token

    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}"}


class RequestSlugAuthenticator:
    def __init__(self, slug: str, token: str):
        self.slug = slug
        self.token = token

    def get_headers(self):
        return {"Authorization": f"{self.slug}:{self.token}"}


class JsonReader:
    def get_json_response(self, request):
        return request.json()


class RequestManagerABC(MontrekManager):
    base_url = "NONESET"

    def __init__(self):
        self.status_code = 0
        self.message = "No get request made"

    @abstractmethod
    def get_response(self, endpoint: str) -> dict | list | pd.DataFrame:
        ...

    def get_endpoint_url(self, endpoint: str) -> str:
        return f"{self.base_url}{endpoint}"


class RequestJsonManager(RequestManagerABC):
    authenticator = RequestAuthenticator()
    json_reader = JsonReader()

    def get_response(self, endpoint: str) -> dict | list:
        endpoint_url = self.get_endpoint_url(endpoint)
        headers = {"User-Agent": "Chrome/128.0.6537.2"}
        headers.update(self.authenticator.get_headers())

        request = requests.get(endpoint_url, headers=headers)
        self.status_code = request.status_code
        if request.ok:
            try:
                json_response = self.json_reader.get_json_response(request)
            except requests.exceptions.JSONDecodeError:
                self.message = "No valid json returned"
                self.status_code = 0
                return {}
            self.message = "OK"
            return json_response
        try:
            request.raise_for_status()
        except requests.exceptions.HTTPError as e:
            self.message = str(e)
        return {}
