from functools import wraps
from unittest import mock


def mock_external_get(response=None):
    """
    Mock all external GET requests at the request_manager boundary.
    """
    if response is None:
        response = mock.Mock(status_code=200, json=lambda: {})

    def decorator(test_func):
        @wraps(test_func)
        def wrapper(*args, **kwargs):
            with mock.patch(
                "requesting.managers.request_manager.requests.get",
                return_value=response,
            ) as mocked_get:
                return test_func(*args, mocked_get=mocked_get, **kwargs)

        return wrapper

    return decorator


PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\x0bIDATx\x9cc`\x00\x00\x00\x02\x00\x01"
    b"\xe2!\xbc3"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


def mock_external_get__report_image(response=None):
    """
    Mock all external GET requests at the request_manager boundary.
    """
    if response is None:
        response = mock.Mock(status_code=200, content=PNG_1X1)

    def decorator(test_func):
        @wraps(test_func)
        def wrapper(*args, **kwargs):
            with mock.patch(
                "reporting.core.reporting_text.requests.get",
                return_value=response,
            ) as mocked_get_image:
                return test_func(*args, mocked_get_image=mocked_get_image, **kwargs)

        return wrapper

    return decorator
