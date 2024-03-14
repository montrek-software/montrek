import requests


class RequestManager:
    base_url = "NONESET"

    def get(self, endpoint):
        return requests.get(f"{self.base_url}{endpoint}", auth=("user", "pass"))
