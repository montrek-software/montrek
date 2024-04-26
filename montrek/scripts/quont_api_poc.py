from api_upload.managers.request_manager import (
    RequestManager,
    RequestSlugAuthenticator,
)


class QontoReqeustManager(RequestManager):
    base_url = "https://thirdparty.qonto.com/v2/"
    authenticator = RequestSlugAuthenticator(
        slug="montrek-ug-haftungsbeschrankt-2537",
        token="",
    )


def run():
    qregman = QontoReqeustManager()
    response_json = qregman.get_json("organization")
    print(response_json)
