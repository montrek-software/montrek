import requests
from base64 import b64encode


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


class RequestManager:
    base_url = "NONESET"
    authenticator = RequestAuthenticator()

    def __init__(self):
        self.status_code = 0
        self.message = "No get request made"

    def get_json(self, endpoint: str) -> dict:
        endpoint_url = f"{self.base_url}{endpoint}"
        request = requests.get(endpoint_url, headers=self.authenticator.get_headers())
        self.status_code = request.status_code
        if request.ok:
            self.message = "OK"
            return request.json()
        try:
            request.raise_for_status()
        except requests.exceptions.HTTPError as e:
            self.message = str(e)
        return {}
