"""The default database, as the DB_* variables configure it.

A class of its own rather than code in settings.py, which runs only once per
process: the tests call it with a config of their own.
"""

import re
from typing import Any

from decouple import Config
from django.core.checks import CheckMessage, Error, register
from django.core.exceptions import ImproperlyConfigured

POSTGRES_ENGINE = "django.db.backends.postgresql"
# Django's backend, asking DB_PASSWORD_PROVIDER for the password of each new
# connection.
PROVIDER_LOGIN_ENGINE = "montrek.db_backend"

_DOTTED_PATH = re.compile(r"^[A-Za-z_]\w*(\.[A-Za-z_]\w*)+$", re.ASCII)


class DatabaseSettings:
    def __init__(self, config: Config) -> None:
        self.config = config

    def default_database(self) -> dict[str, Any]:
        """The DATABASES["default"] entry.

        Postgres only. DB_ENGINE picks how the install reaches it
        (db_yml/<engine>.yml); the env schema check refuses any other value.

        With DB_PASSWORD_PROVIDER the password comes from that function for
        every new connection, so a token that expires is fetched again for the
        next one. The function is not imported here: it comes with an extension
        app, and the apps are not loaded yet while settings.py runs. The
        database system check imports it instead.
        """
        database: dict[str, Any] = {
            "ENGINE": POSTGRES_ENGINE,
            "NAME": self.config("DB_NAME", default="montrek_db"),
            "USER": self.config("DB_USER", default="root"),
            "PASSWORD": self.config("DB_PASSWORD", default=""),
            # In the docker setup: the compose service name (db) and the
            # container's port.
            "HOST": self.config("DB_HOST", default="localhost"),
            "PORT": self.config("DB_PORT", default=5432, cast=int),
            # Keeps a connection per gunicorn thread or worker process for that
            # many seconds instead of opening one per request; the health check
            # replaces one the database has dropped meanwhile.
            "CONN_MAX_AGE": self.config("DB_CONN_MAX_AGE", default=60, cast=int),
            "CONN_HEALTH_CHECKS": True,
        }
        if self.config("DB_ENGINE", default="postgres") == "postgres_ext":
            database["OPTIONS"] = {"sslmode": "require"}
        provider = self.config("DB_PASSWORD_PROVIDER", default="")
        if provider:
            if database["PASSWORD"]:
                raise ImproperlyConfigured(
                    "Set DB_PASSWORD or DB_PASSWORD_PROVIDER, not both."
                )
            if not _DOTTED_PATH.match(provider):
                raise ImproperlyConfigured(
                    "DB_PASSWORD_PROVIDER must be the dotted path of a function, "
                    f"not {provider!r}."
                )
            database["ENGINE"] = PROVIDER_LOGIN_ENGINE
            database["PASSWORD_PROVIDER"] = provider
        return database


@register("montrek_database")
def check_password_provider(app_configs=None, **kwargs) -> list[CheckMessage]:
    """Imports DB_PASSWORD_PROVIDER, so a wrong path fails `migrate`, and with it
    the release step, rather than the first connection of a worker.

    It is not called: that would fetch a password from outside on every
    `manage.py check`, and `migrate` connects right after anyway.
    """
    from django.conf import settings
    from django.utils.module_loading import import_string

    path = settings.DATABASES["default"].get("PASSWORD_PROVIDER")
    if not path:
        return []
    hint = "Check DB_PASSWORD_PROVIDER and that the app providing it is installed."
    try:
        provider = import_string(path)
    except ImportError as error:
        return [
            Error(
                f"DB_PASSWORD_PROVIDER {path} cannot be imported: {error}",
                hint=hint,
                id="montrek.E009",
            )
        ]
    if not callable(provider):
        return [
            Error(
                f"DB_PASSWORD_PROVIDER {path} is not a function.",
                hint=hint,
                id="montrek.E010",
            )
        ]
    return []
