from django.db import connections
from django.test import TestCase
from montrek_example.models.example_models import SatA5
from montrek_example.tests.factories.montrek_example_factories import SatA5Factory


def _read_raw_column(model, pk, field_name, using="default"):
    qs = (
        model._default_manager.using(using)
        .filter(pk=pk)
        .values_list(field_name, flat=True)
    )
    sql, params = qs.query.sql_with_params()

    with connections[using].cursor() as cur:
        cur.execute(sql, params)  # Bandit-safe: no f-strings/format/% here
        (raw_value,) = cur.fetchone()

    return raw_value


class TestEncryptedFields(TestCase):
    def test_field_is_encrypted_in_db(self):
        secret = "secret"  # nosec b105 Test Purposes
        sat = SatA5Factory(secret_field=secret)
        raw = _read_raw_column(SatA5, sat.pk, "secret_field")
        self.assertNotEqual(raw, secret)
