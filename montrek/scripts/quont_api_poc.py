from requesting.managers.request_manager import (
    RequestJsonManager,
)
from requesting.managers.authenticator_managers import RequestSlugAuthenticator


class QontoReqeustManager(RequestJsonManager):
    base_url = "https://thirdparty.qonto.com/v2/"
    authenticator_class = RequestSlugAuthenticator
    request_kwargs = {"bank_account_id": "a6c3b024-abc9-4f67-a003-c6b806077402"}


def run():
    session_data = {
        "slug": "montrek-ug-haftungsbeschrankt-2537",
        "token": "97add3e5181757",
    }

    qregman = QontoReqeustManager(session_data)
    response_json = qregman.get_response("transactions")
    breakpoint()
    print(response_json)
    print(qregman.message)
