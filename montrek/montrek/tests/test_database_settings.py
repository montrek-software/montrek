from django.core.exceptions import ImproperlyConfigured

from montrek.database_settings import (
    PROVIDER_LOGIN_ENGINE,
    POSTGRES_ENGINE,
    DatabaseSettings,
)
from montrek.tests.test_configuration import TEST_DB_PASSWORD, ConfigurationTestCase

PROVIDER = "montrek_example.database.example_password"


class TestDatabaseSettings(ConfigurationTestCase):
    def default_database(self, environ):
        return DatabaseSettings(self.build(environ)).default_database()

    def test_postgres_with_the_password(self):
        database = self.default_database({"DB_PASSWORD": TEST_DB_PASSWORD})
        self.assertEqual(database["ENGINE"], POSTGRES_ENGINE)
        self.assertEqual(database["PASSWORD"], TEST_DB_PASSWORD)
        self.assertNotIn("PASSWORD_PROVIDER", database)
        self.assertNotIn("OPTIONS", database)

    def test_postgres_ext_requires_ssl(self):
        database = self.default_database(
            {"DB_PASSWORD": TEST_DB_PASSWORD, "DB_ENGINE": "postgres_ext"}
        )
        self.assertEqual(database["OPTIONS"], {"sslmode": "require"})

    def test_a_password_provider_switches_the_engine(self):
        database = self.default_database(
            {"DB_PASSWORD_PROVIDER": PROVIDER, "DB_ENGINE": "postgres_ext"}
        )
        self.assertEqual(database["ENGINE"], PROVIDER_LOGIN_ENGINE)
        self.assertEqual(database["PASSWORD_PROVIDER"], PROVIDER)
        self.assertEqual(database["PASSWORD"], "")
        self.assertEqual(database["OPTIONS"], {"sslmode": "require"})

    def test_a_password_and_a_provider_are_refused(self):
        with self.assertRaisesMessage(
            ImproperlyConfigured, "Set DB_PASSWORD or DB_PASSWORD_PROVIDER, not both."
        ):
            self.default_database(
                {"DB_PASSWORD": TEST_DB_PASSWORD, "DB_PASSWORD_PROVIDER": PROVIDER}
            )

    def test_a_provider_that_is_no_dotted_path_is_refused(self):
        for value in ("azure", "provider.", "my-app.password", "a.b c"):
            with (
                self.subTest(value=value),
                self.assertRaisesMessage(
                    ImproperlyConfigured,
                    "DB_PASSWORD_PROVIDER must be the dotted path of a function",
                ),
            ):
                self.default_database({"DB_PASSWORD_PROVIDER": value})

    def test_db_schema_sets_the_search_path(self):
        database = self.default_database(
            {"DB_PASSWORD": TEST_DB_PASSWORD, "DB_SCHEMA": "app_data"}
        )
        self.assertEqual(database["OPTIONS"], {"options": "-c search_path=app_data"})
        self.assertEqual(database["SCHEMA"], "app_data")

    def test_db_schema_with_postgres_ext_keeps_ssl(self):
        database = self.default_database(
            {
                "DB_PASSWORD": TEST_DB_PASSWORD,
                "DB_ENGINE": "postgres_ext",
                "DB_SCHEMA": "app_data",
            }
        )
        self.assertEqual(
            database["OPTIONS"],
            {"options": "-c search_path=app_data", "sslmode": "require"},
        )

    def test_an_empty_db_schema_changes_nothing(self):
        database = self.default_database(
            {"DB_PASSWORD": TEST_DB_PASSWORD, "DB_SCHEMA": ""}
        )
        self.assertNotIn("OPTIONS", database)
        self.assertNotIn("SCHEMA", database)

    def test_a_schema_that_is_no_plain_name_is_refused(self):
        for value in ("App", "1app", "app,public", "app -c x=y", '"app"', "a" * 64):
            with (
                self.subTest(value=value),
                self.assertRaisesMessage(ImproperlyConfigured, "DB_SCHEMA must be"),
            ):
                self.default_database(
                    {"DB_PASSWORD": TEST_DB_PASSWORD, "DB_SCHEMA": value}
                )

    def test_the_longest_plain_name_is_accepted(self):
        database = self.default_database(
            {"DB_PASSWORD": TEST_DB_PASSWORD, "DB_SCHEMA": "a" * 63}
        )
        self.assertEqual(database["SCHEMA"], "a" * 63)
