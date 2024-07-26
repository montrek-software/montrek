from user.tests.factories.montrek_user_factories import MontrekUserFactory


def add_logged_in_user(func):
    def wrapper(self, *args, **kwargs):
        self.user = MontrekUserFactory()
        self.client.force_login(self.user)
        func(self, *args, **kwargs)

    return wrapper
