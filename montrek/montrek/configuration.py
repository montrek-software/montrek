"""Configuration loading for montrek.

One `config` object, shared by `settings.py` and by any app code that needs a
value before Django is configured. It extends `python-decouple` in two ways.

**A missing `.env` is not an error.** `decouple.RepositoryEnv` opens the file in
its constructor, so importing `settings.py` without one raised `FileNotFoundError`
before anything could report a useful message. A container is configured through
`env_file:`/`environment:` and deliberately has no readable `.env` (the repo bind
mount shadows it with `/dev/null`), and CI has none either. The file is one
source among several, so its absence just means that source is empty.

**Values may come from files instead of the environment.** For every key, in
order of precedence:

1. `os.environ[NAME]`
2. `os.environ[NAME_FILE]`, read as a path to a file holding the value
3. `<secrets dir>/name` or `<secrets dir>/NAME`, for each secrets directory:
   `/run/secrets`, where Compose mounts `secrets:` entries, and then the repo's
   own `secrets/`, which is where `make secrets-init` puts them and the only one
   that exists for a non-Docker run on the host
4. the `.env` file
5. the `default=` given at the call site

2 and 3 are what keeps a secret out of `docker inspect`: `env_file:` and
`environment:` values are materialized into the container config on the host and
readable by anyone in the `docker` group, while a file secret is a bind mount
whose *path* is all the config records. `docs/secrets.md` has the full picture,
including what this does not protect against.

An empty secret file counts as unset, so a secret that is declared for a service
but not used by this install (an unset `KEYCLOAK_CLIENT_SECRET`, say) falls
through to the `.env` file or the default rather than silently becoming `""`.
Compose refuses to start when a declared `secrets: file:` is missing, so
`bin/secrets/init-secrets.sh` creates every declared file and leaves the unused
ones empty.
"""

import os
from pathlib import Path

from decouple import Config, RepositoryEnv, Undefined, undefined
from django.core.exceptions import ImproperlyConfigured

# Where Compose mounts `secrets:`.
CONTAINER_SECRETS_DIR = "/run/secrets"

# Where `make secrets-init` writes them, relative to the repository root. Both
# are searched, in this order, so the same settings module works in a container
# and in a `manage.py runserver`/`manage.py test` on the host, which has no
# /run/secrets. Inside a container this path is /montrek/secrets, which the
# compose files shadow with an empty tmpfs -- so it is never the repo copy that
# answers there.
HOST_SECRETS_DIRNAME = "secrets"

# Suffix of the environment variable naming a file to read a value from. The
# convention postgres, mariadb and keycloak already use for their own settings.
FILE_SUFFIX = "_FILE"

# Sentinel distinct from decouple's `undefined`, which doubles as "no default
# was given" in the public API.
_MISSING = object()


class TolerantRepositoryEnv(RepositoryEnv):
    """`RepositoryEnv` that treats an absent or unreadable `.env` as empty."""

    def __init__(self, source, encoding="UTF-8"):
        try:
            super().__init__(source, encoding=encoding)
        except OSError:
            # Also covers the container case, where `.env` exists but is
            # /dev/null: that parses to an empty mapping without raising.
            self.data = {}


class FileAwareConfig(Config):
    """`decouple.Config` that also resolves `NAME_FILE` and mounted secrets."""

    def __init__(self, repository, secrets_dirs=()):
        super().__init__(repository)
        self.secrets_dirs = [Path(directory) for directory in secrets_dirs]
        # settings.py reads some keys several times (LOG_LEVEL, DEPLOY_HOST);
        # one read per file per process is enough.
        self._file_cache = {}

    def get(self, option, default=undefined, cast=undefined):
        value = self._resolve_from_files(option)
        if value is _MISSING:
            # Environment, then `.env`, then the default -- unchanged decouple
            # behaviour, including its UndefinedValueError.
            return super().get(option, default, cast)
        return self._cast(value, cast)

    def _resolve_from_files(self, option):
        """The value for `option` from a file, or `_MISSING`.

        An explicit `NAME` in the environment wins over every file, so a local
        override or a CI variable still takes effect against an install that has
        secret files mounted.
        """
        if option in os.environ:
            return _MISSING

        path = os.environ.get(f"{option}{FILE_SUFFIX}")
        if path:
            # Explicitly pointed at a file: an unreadable one is a deployment
            # error, not a reason to fall back to a stale value elsewhere.
            value = self._read(path, required=True)
            if value:
                return value
            raise ImproperlyConfigured(
                f"{option}{FILE_SUFFIX}={path!r} is empty. Remove the variable "
                f"to fall back to .env, or write the value to that file."
            )

        for directory in self.secrets_dirs:
            for name in (option, option.lower()):
                value = self._read(directory / name, required=False)
                if value:
                    return value

        return _MISSING

    def _read(self, path, required):
        """File contents without the trailing newline, or `""` if unusable."""
        key = str(path)
        if key in self._file_cache:
            return self._file_cache[key]

        try:
            # Trailing newlines only: a value may legitimately start or end with
            # a space, and `printf '%s' > secret` versus `echo > secret` must not
            # produce different passwords.
            value = Path(path).read_text(encoding="UTF-8").rstrip("\r\n")
        except OSError as error:
            if required:
                raise ImproperlyConfigured(
                    f"Cannot read the configured secret file {key!r}: {error}"
                ) from error
            value = ""

        self._file_cache[key] = value
        return value

    def _cast(self, value, cast):
        """Apply `cast` exactly as `decouple.Config.get` would."""
        if isinstance(cast, Undefined):
            return value
        if cast is bool:
            return self._cast_boolean(value)
        return cast(value)


def build_config(env_file, secrets_dirs=None):
    """The `config` callable for `env_file`.

    `secrets_dirs` defaults to `MONTREK_SECRETS_DIR` when that is set -- which
    replaces the search rather than adding to it -- and otherwise to the
    container mount point followed by the repository's own `secrets/`.
    """
    if secrets_dirs is None:
        override = os.environ.get("MONTREK_SECRETS_DIR")
        if override:
            secrets_dirs = [override]
        else:
            secrets_dirs = [
                CONTAINER_SECRETS_DIR,
                Path(env_file).resolve().parent / HOST_SECRETS_DIRNAME,
            ]
    elif isinstance(secrets_dirs, str | Path):
        secrets_dirs = [secrets_dirs]
    return FileAwareConfig(TolerantRepositoryEnv(env_file), secrets_dirs=secrets_dirs)


# The repository root, one level above the Django project root that holds
# manage.py. `.env` lives next to docker-compose.yml.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE = REPO_ROOT / ".env"

config = build_config(ENV_FILE)
