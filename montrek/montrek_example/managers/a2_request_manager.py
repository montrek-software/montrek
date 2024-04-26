from api_upload.managers.request_manager import RequestManager


class A2RequestManager(RequestManager):
    base_url = "http://example.com/api/v1/"

    def get_json(self, endpoint: str) -> dict | list:
        self.status_code = 200
        return [{"field_a2_str": "api value", "field_a2_float": 50.0}]
