from typing import Any
import requests
from requesting.managers.authenticator_managers import RequestUserPasswordAuthenticator
from requesting.managers.request_manager import RequestJsonManager


class A2RequestManager(RequestJsonManager):
    base_url = "http://example.com/api/v1/"
    authenticator_class = RequestUserPasswordAuthenticator

    def get_request(
        self, endpoint_url: str, headers: dict[str, Any]
    ) -> requests.models.Response:
        response = requests.models.Response()
        response.status_code = 200
        return response

    def get_json(self, endpoint: str) -> dict | list:
        self.status_code = 200
        return [
            {"field_a2_str": "api value 1", "field_a2_float": 1.0},
            {"field_a2_str": "api value 2", "field_a2_float": 2.0},
        ]
