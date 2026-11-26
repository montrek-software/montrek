import uuid
from io import StringIO
from unittest import mock, skipUnless

from django.conf import settings
from django.db import ProgrammingError, connection, transaction
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from psycopg2 import sql

from baseclasses.repositories.db.database_schema import DatabaseSchema
from baseclasses.signals import create_database_schema


class DatabaseSchemaTestCase(TestCase):
    """Each test gets a schema name of its own on the default connection; the
    schemas and roles it creates go with the test's transaction."""

    def setUp(self):
        super().setUp()
        self.name = f"test_schema_{uuid.uuid4().hex[:12]}"
        patch = mock.patch.dict(connection.settings_dict, {"SCHEMA": self.name})
        patch.start()
        self.addCleanup(patch.stop)

    def execute(self, statement, params=None):
        with connection.cursor() as cursor:
            cursor.execute(statement, params)

    def schema_exists(self) -> bool:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_namespace WHERE nspname = %s", [self.name])
            return cursor.fetchone() is not None


class TestDatabaseSchema(DatabaseSchemaTestCase):
    def test_creates_a_missing_schema(self):
        self.assertTrue(DatabaseSchema("default").ensure())

        self.assertTrue(self.schema_exists())

    def test_leaves_an_existing_schema_alone(self):
        self.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(self.name)))

        with CaptureQueriesContext(connection) as queries:
            self.assertFalse(DatabaseSchema("default").ensure())

        self.assertFalse(
            any("CREATE" in query["sql"].upper() for query in queries.captured_queries)
        )

    def test_needs_no_create_right_on_the_database_for_an_existing_schema(self):
        role = f"test_role_{uuid.uuid4().hex[:12]}"
        self.execute(sql.SQL("CREATE ROLE {}").format(sql.Identifier(role)))
        self.execute(
            sql.SQL("CREATE SCHEMA {} AUTHORIZATION {}").format(
                sql.Identifier(self.name), sql.Identifier(role)
            )
        )
        self.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))

        # What the lookup avoids: the statement wants the right even so.
        with self.assertRaises(ProgrammingError), transaction.atomic():
            self.execute(
                sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                    sql.Identifier(self.name)
                )
            )
        self.assertFalse(DatabaseSchema("default").ensure())

    def test_without_a_schema_nothing_is_done(self):
        with (
            mock.patch.dict(connection.settings_dict, {"SCHEMA": ""}),
            CaptureQueriesContext(connection) as queries,
        ):
            self.assertFalse(DatabaseSchema("default").ensure())

        self.assertEqual(queries.captured_queries, [])


class TestCreateDatabaseSchemaReceiver(DatabaseSchemaTestCase):
    def test_reports_a_created_schema(self):
        stdout = StringIO()

        create_database_schema(using="default", verbosity=1, stdout=stdout)

        self.assertTrue(self.schema_exists())
        self.assertEqual(stdout.getvalue(), f"  Created schema {self.name}\n")

    def test_is_quiet_about_an_existing_schema(self):
        self.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(self.name)))
        stdout = StringIO()

        create_database_schema(using="default", verbosity=1, stdout=stdout)

        self.assertEqual(stdout.getvalue(), "")


@skipUnless(
    settings.DATABASES["default"].get("SCHEMA"), "Runs on a run with DB_SCHEMA set."
)
class TestMigratedDatabaseSchema(TestCase):
    """The test database itself, migrated with DB_SCHEMA set."""

    def tables_in(self, schema: str) -> list[str]:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname = %s", [schema]
            )
            return [row[0] for row in cursor.fetchall()]

    def test_django_migrations_is_in_the_schema(self):
        schema = settings.DATABASES["default"]["SCHEMA"]

        self.assertIn("django_migrations", self.tables_in(schema))

    def test_public_holds_no_tables(self):
        self.assertEqual(self.tables_in("public"), [])
