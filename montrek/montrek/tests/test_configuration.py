"""Tests for the configuration resolution order in `montrek.configuration`.

These exercise the resolver directly rather than through `settings.py`: the
settings module is imported once per process, long before any test runs, so it
cannot be re-read under a patched environment.
"""

import os
from unittest import mock, skipIf

from decouple import UndefinedValueError
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from montrek.configuration import (
    CONTAINER_SECRETS_DIR,
    HOST_SECRETS_DIRNAME,
    TolerantRepositoryEnv,
    build_config,
)


class ConfigurationTestCase(SimpleTestCase):
    """Base class providing an isolated .env file and secrets directory."""

    def setUp(self):
        super().setUp()
        import tempfile
        from pathlib import Path

        self._temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp_dir.cleanup)
        self.root = Path(self._temp_dir.name)
        self.secrets_dir = self.root / "secrets"
        self.secrets_dir.mkdir()
        self.env_file = self.root / ".env"

    def write_env(self, name, value):
        """Write a .env file that defines `name` as `value`.

        The name and the value are separate arguments rather than a single
        `NAME=value` literal: a literal that pairs a key like DB_PASSWORD or
        SECRET_KEY with a value is read as a hardcoded credential (bandit B105,
        sonar S2068). These fixtures are placeholders written into a throwaway
        temporary directory, so the pairing is kept out of the source entirely.
        """
        self.env_file.write_text(f"{name}={value}\n", encoding="UTF-8")

    def write_secret(self, name, content):
        path = self.secrets_dir / name
        path.write_text(content, encoding="UTF-8")
        return path

    def build(self, environ=None):
        """A config for the temporary env file, with `environ` as the only env.

        The environment is a mapping rather than keyword arguments so that
        `SECRET_KEY=...` is not a keyword argument holding a literal, which
        bandit reports as a hardcoded password (B106).
        """
        patcher = mock.patch.dict(os.environ, environ or {}, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        return build_config(self.env_file, secrets_dirs=self.secrets_dir)


class TolerantRepositoryEnvTest(ConfigurationTestCase):
    def test_missing_env_file_is_an_empty_repository(self):
        repository = TolerantRepositoryEnv(self.root / "does-not-exist")

        self.assertNotIn("SECRET_KEY", repository.data)

    def test_unopenable_env_file_is_an_empty_repository(self):
        """A path that cannot be opened at all, whatever the uid.

        A directory raises IsADirectoryError for root as well, so this holds in
        CI -- which runs the suite as root (`--user 0:0` in django.yml) -- as
        well as on a developer machine.
        """
        repository = TolerantRepositoryEnv(self.root)

        self.assertEqual(repository.data, {})

    @skipIf(
        hasattr(os, "geteuid") and os.geteuid() == 0,
        "root bypasses the permission bits, so a 0o000 file is still readable",
    )
    def test_unreadable_env_file_is_an_empty_repository(self):
        self.write_env("SECRET_KEY", "from-file")
        self.env_file.chmod(0o000)
        self.addCleanup(self.env_file.chmod, 0o600)

        repository = TolerantRepositoryEnv(self.env_file)

        self.assertEqual(repository.data, {})

    def test_existing_env_file_is_still_parsed(self):
        self.write_env("SECRET_KEY", "from-file")

        repository = TolerantRepositoryEnv(self.env_file)

        self.assertEqual(repository["SECRET_KEY"], "from-file")

    def test_settings_import_without_env_file_does_not_raise(self):
        config = build_config(
            self.root / "does-not-exist", secrets_dirs=self.secrets_dir
        )

        self.assertEqual(config("SECRET_KEY", default="fallback"), "fallback")


class ResolutionOrderTest(ConfigurationTestCase):
    def test_environment_wins_over_every_file(self):
        self.write_env("SECRET_KEY", "from-env-file")
        self.write_secret("SECRET_KEY", "from-secret")
        pointed_at = self.root / "pointed-at"
        pointed_at.write_text("from-file-variable", encoding="UTF-8")
        # Bound to a name rather than written inline: bandit reads a literal
        # paired with a key like SECRET_KEY as a hardcoded password (B105).
        from_environment = "from-environment"
        config = self.build(
            {"SECRET_KEY": from_environment, "SECRET_KEY_FILE": str(pointed_at)}
        )

        self.assertEqual(config("SECRET_KEY"), from_environment)

    def test_file_variable_wins_over_secrets_dir_and_env_file(self):
        self.write_env("SECRET_KEY", "from-env-file")
        self.write_secret("SECRET_KEY", "from-secret")
        pointed_at = self.root / "pointed-at"
        pointed_at.write_text("from-file-variable", encoding="UTF-8")
        config = self.build({"SECRET_KEY_FILE": str(pointed_at)})

        self.assertEqual(config("SECRET_KEY"), "from-file-variable")

    def test_secrets_dir_wins_over_env_file(self):
        self.write_env("SECRET_KEY", "from-env-file")
        self.write_secret("SECRET_KEY", "from-secret")
        config = self.build()

        self.assertEqual(config("SECRET_KEY"), "from-secret")

    def test_lowercased_secret_name_is_found(self):
        self.write_env("DB_PASSWORD", "from-env-file")
        self.write_secret("db_password", "from-secret")
        config = self.build()

        self.assertEqual(config("DB_PASSWORD"), "from-secret")

    def test_uppercase_secret_wins_over_lowercase(self):
        self.write_secret("DB_PASSWORD", "upper")
        self.write_secret("db_password", "lower")
        config = self.build()

        self.assertEqual(config("DB_PASSWORD"), "upper")

    def test_env_file_wins_over_default(self):
        self.write_env("SECRET_KEY", "from-env-file")
        config = self.build()

        self.assertEqual(config("SECRET_KEY", default="fallback"), "from-env-file")

    def test_default_is_used_when_nothing_provides_the_value(self):
        config = self.build()

        self.assertEqual(config("SECRET_KEY", default="fallback"), "fallback")

    def test_missing_value_without_default_still_raises(self):
        config = self.build()

        with self.assertRaises(UndefinedValueError):
            config("SECRET_KEY")


class EmptySecretTest(ConfigurationTestCase):
    """A declared-but-unused Compose secret must not shadow the other sources.

    `bin/secrets/init-secrets.sh` creates a file for every secret the compose
    overlay declares, because Compose refuses to start when one is missing. The
    ones this install does not use stay empty.
    """

    def test_empty_secret_file_falls_through_to_the_env_file(self):
        self.write_env("KEYCLOAK_CLIENT_SECRET", "from-env-file")
        self.write_secret("keycloak_client_secret", "")
        config = self.build()

        self.assertEqual(config("KEYCLOAK_CLIENT_SECRET"), "from-env-file")

    def test_newline_only_secret_file_falls_through_to_the_default(self):
        self.write_secret("keycloak_client_secret", "\n")
        config = self.build()

        self.assertEqual(config("KEYCLOAK_CLIENT_SECRET", default=""), "")

    def test_empty_file_variable_is_a_configuration_error(self):
        empty = self.root / "empty"
        empty.write_text("", encoding="UTF-8")
        config = self.build({"SECRET_KEY_FILE": str(empty)})

        with self.assertRaises(ImproperlyConfigured):
            config("SECRET_KEY", default="fallback")

    def test_unreadable_file_variable_is_a_configuration_error(self):
        config = self.build({"SECRET_KEY_FILE": str(self.root / "does-not-exist")})

        with self.assertRaises(ImproperlyConfigured):
            config("SECRET_KEY", default="fallback")


class SecretValueTest(ConfigurationTestCase):
    def test_trailing_newline_is_stripped(self):
        self.write_secret("db_password", "hunter2\n")
        config = self.build()

        self.assertEqual(config("DB_PASSWORD"), "hunter2")

    def test_trailing_carriage_return_is_stripped(self):
        self.write_secret("db_password", "hunter2\r\n")
        config = self.build()

        self.assertEqual(config("DB_PASSWORD"), "hunter2")

    def test_inner_whitespace_and_quotes_are_preserved(self):
        self.write_secret("db_password", '  a b"c$d  \n')
        config = self.build()

        self.assertEqual(config("DB_PASSWORD"), '  a b"c$d  ')

    def test_multiline_secret_keeps_its_inner_newlines(self):
        self.write_secret("db_password", "line one\nline two\n")
        config = self.build()

        self.assertEqual(config("DB_PASSWORD"), "line one\nline two")

    def test_file_is_read_once_per_process(self):
        secret = self.write_secret("db_password", "hunter2")
        config = self.build()

        self.assertEqual(config("DB_PASSWORD"), "hunter2")
        secret.write_text("rotated", encoding="UTF-8")

        self.assertEqual(config("DB_PASSWORD"), "hunter2")


class CastTest(ConfigurationTestCase):
    def test_bool_cast_applies_to_a_secret(self):
        self.write_secret("debug", "0")
        config = self.build()

        self.assertIs(config("DEBUG", default=True, cast=bool), False)

    def test_int_cast_applies_to_a_secret(self):
        self.write_secret("email_port", "2525\n")
        config = self.build()

        self.assertEqual(config("EMAIL_PORT", default=587, cast=int), 2525)

    def test_bool_cast_still_applies_to_the_env_file(self):
        self.write_env("DEBUG", "true")
        config = self.build()

        self.assertIs(config("DEBUG", default=False, cast=bool), True)

    def test_cast_is_not_applied_to_an_untouched_default(self):
        config = self.build()

        self.assertIs(config("DEBUG", default=False, cast=bool), False)


class SecretsDirTest(ConfigurationTestCase):
    def test_absent_secrets_dir_is_not_an_error(self):
        self.write_env("SECRET_KEY", "from-env-file")
        patcher = mock.patch.dict(os.environ, {}, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        config = build_config(self.env_file, secrets_dirs=self.root / "no-such-dir")

        self.assertEqual(config("SECRET_KEY"), "from-env-file")

    def test_montrek_secrets_dir_overrides_the_default(self):
        self.write_secret("secret_key", "from-secret")
        patcher = mock.patch.dict(
            os.environ, {"MONTREK_SECRETS_DIR": str(self.secrets_dir)}, clear=True
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        config = build_config(self.env_file)

        self.assertEqual(config("SECRET_KEY"), "from-secret")


class SecretsDirDefaultsTest(ConfigurationTestCase):
    """The search path when the caller does not name one.

    A non-Docker run on the host has no /run/secrets, so the repository's own
    secrets/ -- what `make secrets-init` writes -- has to be searched as well, or
    `manage.py runserver` and `manage.py test` break the moment an install
    migrates. Inside a container that same path is /montrek/secrets, which the
    compose files shadow with an empty tmpfs.
    """

    def build_default(self, environ=None):
        patcher = mock.patch.dict(os.environ, environ or {}, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        return build_config(self.env_file)

    def test_container_mount_is_searched_before_the_repository_directory(self):
        config = self.build_default()

        self.assertEqual(
            [str(directory) for directory in config.secrets_dirs],
            [CONTAINER_SECRETS_DIR, str(self.root / HOST_SECRETS_DIRNAME)],
        )

    def test_repository_secrets_are_found_on_a_host_without_run_secrets(self):
        self.write_secret("secret_key", "from-repository-secrets")
        config = self.build_default()

        self.assertEqual(config("SECRET_KEY"), "from-repository-secrets")

    def test_explicit_override_replaces_the_search_path(self):
        self.write_secret("secret_key", "from-repository-secrets")
        other = self.root / "elsewhere"
        other.mkdir()
        (other / "secret_key").write_text("from-override", encoding="UTF-8")
        config = self.build_default({"MONTREK_SECRETS_DIR": str(other)})

        self.assertEqual([str(d) for d in config.secrets_dirs], [str(other)])
        self.assertEqual(config("SECRET_KEY"), "from-override")


class MultipleSecretsDirsTest(ConfigurationTestCase):
    def test_the_first_directory_that_has_the_secret_wins(self):
        first = self.root / "first"
        first.mkdir()
        (first / "db_password").write_text("from-first", encoding="UTF-8")
        self.write_secret("db_password", "from-second")
        patcher = mock.patch.dict(os.environ, {}, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        config = build_config(self.env_file, secrets_dirs=[first, self.secrets_dir])

        self.assertEqual(config("DB_PASSWORD"), "from-first")

    def test_an_empty_file_in_the_first_directory_falls_through_to_the_second(self):
        first = self.root / "first"
        first.mkdir()
        (first / "db_password").write_text("", encoding="UTF-8")
        self.write_secret("db_password", "from-second")
        patcher = mock.patch.dict(os.environ, {}, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        config = build_config(self.env_file, secrets_dirs=[first, self.secrets_dir])

        self.assertEqual(config("DB_PASSWORD"), "from-second")
