from functools import wraps

from user.tests.factories.montrek_user_factories import MontrekUserFactory


def add_logged_in_user(func=None, *, password=None):
    """
    Decorator that logs in a test user before calling the test function.
    Can be used with or without arguments:

        @add_logged_in_user
        def something(...):
            ...

        @add_logged_in_user(password="S3cret!123")
        def something(...):
            ...
    """

    def decorator(test_func):
        @wraps(test_func)
        def wrapper(self, *args, **kwargs):
            if password:
                self.user = MontrekUserFactory(password=password)
            else:
                self.user = MontrekUserFactory()
            self.client.force_login(self.user)
            return test_func(self, *args, **kwargs)

        return wrapper

    # Case 1: Used without parentheses → @add_logged_in_user
    if func and callable(func):
        return decorator(func)

    # Case 2: Used with arguments → @add_logged_in_user(password="...")
    return decorator
