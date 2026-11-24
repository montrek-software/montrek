"""The DatabaseWrapper of the `montrek.db_backend` engine."""

from django.core.exceptions import ImproperlyConfigured
from django.db.backends.postgresql import base
from django.utils.module_loading import import_string


class DatabaseWrapper(base.DatabaseWrapper):
    """Asks the password provider for the password of every new connection.

    Django calls `get_connection_params()` for each connection it opens, so a
    short-lived token is fetched again whenever a connection is replaced. An
    open connection stays valid after its token expires: the database checks
    the password only when it accepts a connection.

    A connection pool (OPTIONS["pool"]) would take the parameters once, with a
    token that expires, so it is refused.
    """

    def get_connection_params(self) -> dict:
        if self.settings_dict["OPTIONS"].get("pool"):
            raise ImproperlyConfigured(
                "DB_PASSWORD_PROVIDER does not work with a connection pool."
            )
        params = super().get_connection_params()
        provider = import_string(self.settings_dict["PASSWORD_PROVIDER"])
        params["password"] = provider()
        return params
