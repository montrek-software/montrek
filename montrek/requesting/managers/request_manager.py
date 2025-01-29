from abc import abstractmethod
from time import sleep
from typing import Any, Callable

import pandas as pd
import requests
from baseclasses.managers.montrek_manager import MontrekManager
from requesting.managers.authenticator_managers import (
    NoAuthenticator,
    RequestAuthenticator,
)


from functools import wraps


class JsonReader:
    def get_json_response(self, request):
        return request.json()


class RequestManagerABC(MontrekManager):
    base_url: str = "NONESET"

    def __init__(self, session_data: dict[str, Any]):
        self.session_data = session_data
        self.status_code = 0
        self.message = "No get request made"

    @abstractmethod
    def get_response(self, endpoint: str) -> dict | list | pd.DataFrame:
        ...

    @abstractmethod
    def post_response(self, endpoint: str, data: dict) -> dict | list | pd.DataFrame:
        ...

    def get_endpoint_url(self, endpoint: str) -> str:
        return f"{self.base_url}{endpoint}"


class RequestJsonManager(RequestManagerABC):
    json_reader = JsonReader()
    authenticator_class: type[RequestAuthenticator] = NoAuthenticator
    request_kwargs = {}
    no_of_retries = 5
    sleep_time = 2

    def __init__(self, session_data: dict[str, Any]):
        super().__init__(session_data)
        self.authenticator = self.authenticator_class(session_data)

    def retry_on_failure(method: Callable) -> Callable:
        """Decorator to handle retry logic."""

        @wraps(method)
        def wrapper(self, *args, **kwargs):
            for _ in range(self.no_of_retries):
                try:
                    return method(self, *args, **kwargs)
                except (
                    requests.exceptions.RequestException,
                    requests.exceptions.ChunkedEncodingError,
                ) as e:
                    sleep(self.sleep_time)
            self.message = f"No request made after {self.no_of_retries} attempts"
            self.status_code = 0
            return None

        return wrapper

    def process_response(method: Callable) -> Callable:
        """Decorator to handle response processing and JSON extraction."""

        @wraps(method)
        def wrapper(self, *args, **kwargs):
            request = method(self, *args, **kwargs)
            if request is None:
                return {}

            self.status_code = request.status_code
            if request.ok:
                try:
                    json_response = self.json_reader.get_json_response(request)
                    self.message = "OK"
                    return json_response
                except requests.exceptions.JSONDecodeError:
                    self.message = "No valid json returned"
                    self.status_code = 0
                    return {}
            try:
                request.raise_for_status()
            except requests.exceptions.HTTPError as e:
                self.message = str(e)
            return {}

        return wrapper

    @retry_on_failure
    @process_response
    def get_response(self, endpoint: str) -> dict | list:
        endpoint_url = self.get_endpoint_url(endpoint)
        headers = self.get_headers()
        return self.get_request(endpoint_url, headers)

    @retry_on_failure
    @process_response
    def post_response(self, endpoint: str, data: dict) -> dict | list | pd.DataFrame:
        endpoint_url = self.get_endpoint_url(endpoint)
        headers = self.get_headers()
        return self.post_request(endpoint_url, headers, data)

    def get_request(
        self, endpoint_url: str, headers: dict[str, Any]
    ) -> requests.models.Response:
        return requests.get(
            endpoint_url, self.request_kwargs, headers=headers, timeout=30
        )

    def post_request(
        self, endpoint_url: str, headers: dict[str, Any], data: dict
    ) -> requests.models.Response:
        return requests.post(
            endpoint_url, self.request_kwargs, headers=headers, files=data, timeout=30
        )

    def get_headers(self) -> dict[str, Any]:
        headers = {"User-Agent": "Chrome/128.0.6537.2", "Accept": "application/json"}
        headers.update(self.authenticator.get_headers())
        return headers
