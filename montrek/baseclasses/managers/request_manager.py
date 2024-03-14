import requests
from dataclasses import dataclass


@dataclass
class RequestAuthenticator:
    user: str
    password: str


class RequestManager:
    base_url = "NONESET"
    authenticator = RequestAuthenticator(user="nouser", password="")

    def __init__(self):
        self.status_code = 0
        self.message = "No get request made"

    def get_json(self, endpoint: str) -> dict:
        endpoint_url = f"{self.base_url}{endpoint}"
        request = requests.get(
            endpoint_url, auth=(self.authenticator.user, self.authenticator.password)
        )
        self.status_code = request.status_code
        if request.ok:
            self.message = "OK"
            return request.json()
        try:
            request.raise_for_status()
        except requests.exceptions.HTTPError as e:
            self.message = str(e)
        return {}
