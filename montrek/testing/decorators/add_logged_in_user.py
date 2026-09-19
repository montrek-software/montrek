from functools import wraps

from user.managers.user_group_manager import create_permission
from user.tests.factories.montrek_user_factories import MontrekUserFactory


def add_logged_in_user(func=None, *, password=None, permissions=None):
    """
    Decorator that logs in a test user before calling the test function.
    Can be used with or without arguments:

        @add_logged_in_user
        def something(...):
            ...

        @add_logged_in_user(password="S3cret!123")
        def something(...):
            ...

    ``permissions`` takes the permission enum members the user should hold, for
    a test that drives views of a restricted app. Without them the user holds
    nothing, the view's gate refuses and the middleware redirects, so the test
    sees a 302 where it expected the page:

        @add_logged_in_user(permissions=[AssetManagementPermissions.CAN_CREATE])
        def something(...):
            ...

    Tests that do not go through a view - repository and manager tests - need
    no permissions, since the gate sits on the view.
    """

    def decorator(test_func):
        @wraps(test_func)
        def wrapper(self, *args, **kwargs):
            if password:
                self.user = MontrekUserFactory(password=password)
            else:
                self.user = MontrekUserFactory()
            if permissions:
                self.user.user_permissions.set(
                    [create_permission(permission) for permission in permissions]
                )
            self.client.force_login(self.user)
            return test_func(self, *args, **kwargs)

        return wrapper

    # Case 1: Used without parentheses → @add_logged_in_user
    if func and callable(func):
        return decorator(func)

    # Case 2: Used with arguments → @add_logged_in_user(password="...")
    return decorator
