from django.db import connections
from psycopg2 import sql


class DatabaseSchema:
    """The schema a database connection keeps its tables in, DB_SCHEMA.

    Django creates no schemas, and ``manage.py test`` builds a fresh test
    database on every run, so ``migrate`` creates the schema before it creates
    its first table.
    """

    def __init__(self, using: str) -> None:
        self.connection = connections[using]
        self.name: str = self.connection.settings_dict.get("SCHEMA", "")

    def ensure(self) -> bool:
        """Creates the schema if it is missing; True if it did.

        Looked up first rather than created with IF NOT EXISTS: PostgreSQL
        demands the CREATE right on the database for that statement even when
        the schema exists, and a role that owns its schema may lack that right.
        """
        if not self.name or self.exists():
            return False
        with self.connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(self.name))
            )
        return True

    def exists(self) -> bool:
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_namespace WHERE nspname = %s", [self.name])
            return cursor.fetchone() is not None
