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
