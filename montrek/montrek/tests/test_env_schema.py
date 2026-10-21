"""Tests for the environment schema in `montrek.env_schema`.

Like the configuration tests, these drive the checks with their own `config`
built over a temporary `.env` and secrets directory, because `settings.py` is
imported once per process before any test runs.
"""

import json
import os
import re
import subprocess  # nosec B404
import sys
from pathlib import Path
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from montrek.configuration import build_config
from montrek.env_schema import (
    CORE_SCHEMA_FILE,
    check_environment,
    find_problems,
    find_configured_keys,
    load_schema,
    raise_for_invalid_settings,
)
from montrek.tests.test_configuration import ConfigurationTestCase

SETTINGS_FILE = Path(__file__).resolve().parent.parent / "settings.py"


class TestCoreSchema(SimpleTestCase):
    def test_core_schema_loads(self):
        schema = load_schema(CORE_SCHEMA_FILE)
        self.assertTrue(schema["SECRET_KEY"].required)
        self.assertTrue(schema["SECRET_KEY"].secret)

    def test_every_setting_is_declared_with_app_scope(self):
        schema = load_schema(CORE_SCHEMA_FILE)
        read = set(re.findall(r'config\(\s*"([A-Z0-9_]+)"', SETTINGS_FILE.read_text()))
        self.assertTrue(read)
        self.assertEqual(read - set(schema), set())
        self.assertEqual({name for name in read if schema[name].scope != "app"}, set())


class SchemaTestCase(ConfigurationTestCase):
    def write_schema(self, content):
        path = self.root / "env.schema.toml"
        path.write_text(content)
        return path


class TestLoadSchema(SchemaTestCase):
    def test_reads_all_fields(self):
        path = self.write_schema(
            '[MODE]\ntype = "choice"\nchoices = ["a", "b"]\nrequired = true\n'
            'secret = true\nscope = "compose"\ndefault = "a"\ndescription = "Mode."\n'
        )
        variable = load_schema(path)["MODE"]
        self.assertEqual(variable.choices, ("a", "b"))
        self.assertTrue(variable.required)
        self.assertTrue(variable.secret)
        self.assertEqual(variable.scope, "compose")

    def test_rejects_invalid_entries(self):
        invalid = {
            "unknown field": '[A]\ntype = "str"\ndescription = "x"\ncolour = "red"\n',
            "unknown type": '[A]\ntype = "float"\ndescription = "x"\n',
            "unknown scope": '[A]\ntype = "str"\ndescription = "x"\nscope = "k8s"\n',
            "choice without choices": '[A]\ntype = "choice"\ndescription = "x"\n',
            "choices without choice": (
                '[A]\ntype = "str"\nchoices = ["a"]\ndescription = "x"\n'
            ),
            "no description": '[A]\ntype = "str"\n',
        }
        for case, content in invalid.items():
            with self.subTest(case), self.assertRaises(ImproperlyConfigured):
                load_schema(self.write_schema(content))


class TestFindProblems(SchemaTestCase):
    def setUp(self):
        super().setUp()
        self.schema = load_schema(
            self.write_schema(
                '[TOKEN]\ntype = "str"\nrequired = true\nsecret = true\n'
                'description = "The token."\n'
                '[COUNT]\ntype = "int"\ndescription = "x"\n'
                '[ENABLED]\ntype = "bool"\ndescription = "x"\n'
                '[MODE]\ntype = "choice"\nchoices = ["a", "b"]\ndescription = "x"\n'
                '[HOSTS]\ntype = "csv"\ndescription = "x"\n'
            )
        )

    def problems(self):
        config = build_config(self.env_file, secrets_dirs=self.secrets_dir)
        return find_problems(self.schema, config)

    def test_valid_values_pass(self):
        self.isolate_environment(
            {
                "TOKEN": "t",
                "COUNT": "3",
                "ENABLED": "on",
                "MODE": "b",
                "HOSTS": "a.example, b.example",
            }
        )
        self.assertEqual(self.problems(), [])

    def test_only_required_values_must_be_set(self):
        self.assertEqual(
            self.problems(), ["TOKEN is required and must not be empty: The token."]
        )

    def test_empty_required_value_counts_as_missing(self):
        self.isolate_environment({"TOKEN": "", "COUNT": "3"})
        self.assertEqual(
            self.problems(), ["TOKEN is required and must not be empty: The token."]
        )

    def test_required_value_from_a_secret_file(self):
        (self.secrets_dir / "token").write_text("t\n")
        self.assertEqual(self.problems(), [])

    def test_reports_every_invalid_value(self):
        self.isolate_environment(
            {"TOKEN": "t", "COUNT": "three", "ENABLED": "maybe", "MODE": "c"}
        )
        problems = self.problems()
        self.assertEqual(len(problems), 3)
        self.assertIn("COUNT must be an integer, got 'three'.", problems)
        self.assertTrue(
            any(p.startswith("ENABLED must be a boolean") for p in problems)
        )
        self.assertIn("MODE must be one of a, b, got 'c'.", problems)

    def test_secret_values_are_not_shown(self):
        self.schema = load_schema(
            self.write_schema(
                '[PORT]\ntype = "int"\nsecret = true\ndescription = "x"\n'
            )
        )
        self.isolate_environment({"PORT": "hunter2"})
        [problem] = self.problems()
        self.assertNotIn("hunter2", problem)


class TestRaiseForInvalidSettings(ConfigurationTestCase):
    def config(self):
        return build_config(self.env_file, secrets_dirs=self.secrets_dir)

    def test_lists_all_problems_at_once(self):
        self.isolate_environment({"DB_PORT": "x", "DEBUG": "sometimes"})
        with self.assertRaises(ImproperlyConfigured) as raised:
            raise_for_invalid_settings(self.config())
        message = str(raised.exception)
        for name in ("SECRET_KEY", "DB_PASSWORD", "DB_PORT", "DEBUG"):
            self.assertIn(f"- {name} ", message)

    def test_passes_with_the_required_values(self):
        self.env_file.write_text("SECRET_KEY=s\n")
        (self.secrets_dir / "db_password").write_text("p")
        raise_for_invalid_settings(self.config())

    def test_ignores_compose_scope(self):
        self.isolate_environment(
            {"SECRET_KEY": "s", "DB_PASSWORD": "p", "GUNICORN_WORKERS": "many"}
        )
        raise_for_invalid_settings(self.config())


class TestFindConfiguredKeys(ConfigurationTestCase):
    def test_reads_env_file_and_secrets_dir(self):
        self.env_file.write_text("SECRET_KEY=s\n")
        (self.secrets_dir / "db_password").write_text("p")
        (self.secrets_dir / "sqlproxy-key.json").write_text("{}")
        (self.secrets_dir / ".gitkeep").write_text("")
        config = build_config(self.env_file, secrets_dirs=self.secrets_dir)
        self.assertEqual(
            find_configured_keys(config),
            [("SECRET_KEY", ".env"), ("DB_PASSWORD", str(self.secrets_dir))],
        )

    def test_ignores_the_environment(self):
        self.isolate_environment({"SOMETHING_ELSE": "x"})
        config = build_config(self.env_file, secrets_dirs=self.secrets_dir)
        self.assertEqual(find_configured_keys(config), [])


class TestCheckEnvironment(ConfigurationTestCase):
    def run_check(self):
        config = build_config(self.env_file, secrets_dirs=self.secrets_dir)
        with mock.patch("montrek.configuration.config", config):
            return check_environment()

    def test_warns_about_compose_scope_unknown_keys_and_build_credentials(self):
        self.env_file.write_text("GUNICORN_WORKERS=many\nDEPLOY_HOTS=x\nGIT_PAT=t\n")
        (self.secrets_dir / "db_pasword").write_text("p")
        messages = [(message.id, message.msg) for message in self.run_check()]
        self.assertEqual(
            [(id_, msg.split()[0]) for id_, msg in messages],
            [
                ("montrek.W001", "GUNICORN_WORKERS"),
                ("montrek.W002", "DEPLOY_HOTS"),
                ("montrek.W003", "GIT_PAT"),
                ("montrek.W002", "DB_PASWORD"),
            ],
        )

    def test_known_runtime_keys_pass(self):
        self.env_file.write_text("SECRET_KEY=s\nGUNICORN_WORKERS=2\n")
        (self.secrets_dir / "db_password").write_text("p")
        self.assertEqual(self.run_check(), [])

    def test_extension_schema_problems_are_errors(self):
        app_dir = self.root / "some_app"
        app_dir.mkdir()
        (app_dir / "env.schema.toml").write_text(
            '[SOME_APP_TOKEN]\ntype = "str"\nrequired = true\ndescription = "x"\n'
        )
        app_config = mock.Mock(path=str(app_dir))
        with mock.patch("django.apps.apps.get_app_configs", return_value=[app_config]):
            messages = self.run_check()
            self.assertEqual([message.id for message in messages], ["montrek.E008"])

            self.env_file.write_text("SOME_APP_TOKEN=t\n")
            self.assertEqual(self.run_check(), [])

    def test_extension_variables_follow_their_scope(self):
        app_dir = self.root / "some_app"
        app_dir.mkdir()
        (app_dir / "env.schema.toml").write_text(
            '[SOME_APP_WORKERS]\ntype = "int"\nscope = "compose"\ndescription = "x"\n'
            '[SOME_APP_TOKEN]\ntype = "int"\nscope = "build"\ndescription = "x"\n'
        )
        self.isolate_environment({"SOME_APP_WORKERS": "many", "SOME_APP_TOKEN": "t"})
        app_config = mock.Mock(path=str(app_dir))
        with mock.patch("django.apps.apps.get_app_configs", return_value=[app_config]):
            messages = self.run_check()
        self.assertEqual(
            [(message.id, message.msg.split()[0]) for message in messages],
            [("montrek.W001", "SOME_APP_WORKERS")],
        )

    def test_extension_cannot_redeclare_a_core_variable(self):
        app_dir = self.root / "some_app"
        app_dir.mkdir()
        (app_dir / "env.schema.toml").write_text(
            '[DB_PORT]\ntype = "str"\ndescription = "x"\n'
        )
        app_config = mock.Mock(path=str(app_dir))
        with (
            mock.patch("django.apps.apps.get_app_configs", return_value=[app_config]),
            self.assertRaises(ImproperlyConfigured),
        ):
            self.run_check()


class TestExtraHostsAndOrigins(SimpleTestCase):
    """The settings are read once per process, so this imports them in a new one."""

    def test_extra_values_are_added_to_the_derived_ones(self):
        environ = {
            **os.environ,
            "EXTRA_ALLOWED_HOSTS": "app.example.com, lb.example.com",
            "EXTRA_CSRF_TRUSTED_ORIGINS": "https://app.example.com",
        }
        output = subprocess.run(  # noqa: S603  # nosec B603
            [
                sys.executable,
                "-c",
                "import json; from montrek import settings; print(json.dumps("
                "[settings.ALLOWED_HOSTS, settings.CSRF_TRUSTED_ORIGINS]))",
            ],
            cwd=SETTINGS_FILE.parent.parent,
            env=environ,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        allowed_hosts, csrf_trusted_origins = json.loads(output.splitlines()[-1])
        self.assertIn("localhost", allowed_hosts)
        self.assertEqual(allowed_hosts[-2:], ["app.example.com", "lb.example.com"])
        self.assertEqual(csrf_trusted_origins[-1], "https://app.example.com")
