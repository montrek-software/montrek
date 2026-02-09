from bs4 import BeautifulSoup
from django.db import connections
from django.test import TestCase
from montrek_example.managers.montrek_example_managers import (
    CompactHubAManager,
    SatA5HistoryManager,
    SatA5Manager,
)
from montrek_example.models.example_models import SatA5
from montrek_example.repositories.hub_a_repository import HubARepository5
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
    def setUp(self):
        self.secret = "secret"  # nosec b105 Test Purposes # noqa
        self.sat = SatA5Factory.create(secret_field=self.secret)
        self.manager = SatA5Manager()

    def test_field_is_encrypted_in_db(self):
        raw = _read_raw_column(SatA5, self.sat.pk, "secret_field")
        self.assertNotEqual(raw, self.secret)

    def test_field_is_decrypted_by_django(self):
        repo = HubARepository5({})
        qs = repo.receive()
        self.assertEqual(qs.first().secret_field, self.secret)

    def test_field_is_hidden_in_html(self):
        html = self.manager.to_html()
        soup = BeautifulSoup(html, "html.parser")
        tds = [td.get_text(strip=True) for td in soup.find_all("td")]
        self.assertNotIn("secret", tds)
        self.assertIn("******", tds)

    def test_field_is_hidden_in_latex(self):
        latex = self.manager.to_latex()
        self.assertNotIn("& \\color{black} secret\\\\", latex)
        self.assertIn("& \\color{black} ******\\\\", latex)

    def test_secret_in_history_manager_in_html(self):
        history_manager = SatA5HistoryManager({}, "History", SatA5.objects.all())
        html = history_manager.to_html()
        soup = BeautifulSoup(html, "html.parser")
        tds = [td.get_text(strip=True) for td in soup.find_all("td")]
        self.assertNotIn("secret", tds)
        self.assertIn("******", tds)


class TestEncryptedFieldsWithNone(TestCase):
    def setUp(self):
        self.secret = None  # nosec b105 Test Purposes
        self.sat = SatA5Factory.create(secret_field=self.secret)
        self.manager = SatA5Manager()

    def test_field_is_hidden_in_html(self):
        html = self.manager.to_html()
        soup = BeautifulSoup(html, "html.parser")
        tds = [td.get_text(strip=True) for td in soup.find_all("td")]
        self.assertIn("", tds)

    def test_field_is_hidden_in_latex(self):
        latex = self.manager.to_latex()
        self.assertIn("& \\color{black} \\\\", latex)

    def test_secret_in_history_manager_in_html(self):
        history_manager = SatA5HistoryManager({}, "History", SatA5.objects.all())
        html = history_manager.to_html()
        soup = BeautifulSoup(html, "html.parser")
        tds = [td.get_text(strip=True) for td in soup.find_all("td")]
        self.assertIn("", tds)


class TestManagerFunctionality(TestCase):
    def test_renamings_in_filter_fields(self):
        manager = CompactHubAManager()
        field_choices = manager.get_std_queryset_field_choices()
        for field, description in field_choices:
            if field == "field_a2_float":
                self.assertEqual(description, "Renamed Label")
            else:
                self.assertEqual(description, field.replace("_", " ").title())
