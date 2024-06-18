import datetime
from api_upload.managers.request_manager import RequestJsonManager


class A2RequestManager(RequestJsonManager):
    base_url = "http://example.com/api/v1/"

    def get_json(self, endpoint: str) -> dict | list:
        now = datetime.datetime.now()
        if now.second % 2 == 0:
            self.status_code = 0
            self.message = "Dummy API: Internal Server Error"
            return {}
        self.status_code = 200
        return [
            {"field_a2_str": "api value 1", "field_a2_float": 1.0},
            {"field_a2_str": "api value 2", "field_a2_float": 2.0},
        ]
