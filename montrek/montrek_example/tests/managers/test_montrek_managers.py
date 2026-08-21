from bs4 import BeautifulSoup
from django.db import connections
from django.test import TestCase
from montrek_example.managers.montrek_example_managers import (
    CompactHubAManager,
    HubAManager,
    HubBManager,
    SatA5HistoryManager,
    SatA5Manager,
)
from montrek_example.models.example_models import SatA5
from montrek_example.repositories.hub_a_repository import HubARepository5
from montrek_example.tests.factories.montrek_example_factories import SatA5Factory

from baseclasses.managers.montrek_manager import (
    MontrekManager,
    MontrekManagerNotImplemented,
)
from montrek_example.models import example_models as me_models
from montrek_example.repositories.hub_c_repository import HubCRepository
from montrek_example.tests.factories import montrek_example_factories as me_factories


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
        self.assertIn("& \\color{textdark} ******\\\\", latex)

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
        self.assertIn("& \\color{textdark} \\\\", latex)

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


class TestTableElementFilterFields(TestCase):
    """Table managers offer their own columns as filter fields.

    ``CompactHubAManager`` opts out with ``has_table_elements_filter_field`` and
    keeps the repository fields (see ``test_renamings_in_filter_fields``); the
    other managers derive fields and labels from their table elements.
    """

    def test_filter_fields_are_the_columns_of_the_table(self):
        manager = HubAManager()
        self.assertEqual(
            sorted(manager.get_all_fields()),
            [
                "field_a1_int",
                "field_a1_str",
                "field_a2_float",
                "field_a2_str",
                "field_b1_str",
                "individual_field",
            ],
        )

    def test_filter_labels_are_the_column_headers(self):
        manager = HubAManager()
        field_choices = dict(manager.get_std_queryset_field_choices())
        self.assertEqual(field_choices["field_a1_str"], "A1 String")
        self.assertEqual(field_choices["individual_field"], "TestField")

    def test_column_header_wins_over_the_repository_renaming(self):
        # ``HubARepository`` renames ``field_a2_float`` to "Renamed Label"; the
        # column header the user actually sees is "A2 Float".
        manager = HubAManager()
        field_choices = dict(manager.get_std_queryset_field_choices())
        self.assertEqual(field_choices["field_a2_float"], "A2 Float")

    def test_repository_only_fields_are_not_offered(self):
        # ``field_b1_date`` is annotated by the repository but has no column.
        manager = HubAManager()
        self.assertIn("field_b1_date", manager.repository.get_all_fields())
        self.assertNotIn("field_b1_date", manager.get_all_fields())

    def test_icon_link_columns_are_not_offered(self):
        # View/Update/Delete and the inline-edit pencil carry no field.
        manager = HubAManager()
        field_choices = manager.get_std_queryset_field_choices()
        self.assertNotIn("", [field for field, _ in field_choices])
        self.assertNotIn("View", [description for _, description in field_choices])

    def test_link_columns_contribute_the_field_they_display(self):
        # "D1 String" is a link, "Linked D Objects" a link list: both display
        # ``field_d1_str`` through ``text`` rather than through ``attr``.
        manager = HubBManager()
        fields = manager.get_all_fields()
        self.assertEqual(fields.count("field_d1_str"), 1)
        # Both columns claim the field; the last one labels it.
        field_choices = dict(manager.get_std_queryset_field_choices())
        self.assertEqual(field_choices["field_d1_str"], "Linked D Objects")

    def test_filter_choices_are_sorted_by_label(self):
        manager = HubBManager()
        descriptions = [
            description for _, description in manager.get_std_queryset_field_choices()
        ]
        self.assertEqual(descriptions, sorted(descriptions, key=str.casefold))

    def test_columns_computed_in_python_are_offered_without_a_queryset_field(self):
        """Known gap: a column computed in Python has nothing to filter on.

        ``ExampleIndividualTableElement`` derives its value in ``get_value`` and
        its ``attr`` never reaches the queryset, so "TestField" is offered as a
        filter field although the repository cannot filter by it.
        """
        manager = HubAManager()
        self.assertIn("individual_field", manager.get_all_fields())
        self.assertNotIn("individual_field", manager.repository.get_all_fields())


class HubCManager(MontrekManager):
    repository_class = HubCRepository


class TestMontrekManager(TestCase):
    def test_not_implemented(self):
        self.assertRaises(NotImplementedError, MontrekManager().download)
        self.assertRaises(NotImplementedError, MontrekManager().get_filename)
        self.assertRaises(NotImplementedError, MontrekManagerNotImplemented)

    def test_collect_messages__no_repository(self):
        manager = MontrekManager()
        manager.collect_messages()
        self.assertEqual(manager.messages, [])


class TestMontrekManagerGetObjectFromPk(TestCase):
    """``get_object_from_pk`` resolves a pk via its hub, not by row identity.

    A HubValueDate pk taken from a URL need not be one of the rows the
    repository currently returns: a repository that annotates a time series
    drops the null-date HubValueDate as soon as a dated one exists. Resolving
    through the hub keeps such a pk usable.
    """

    def setUp(self):
        self.hub = me_factories.HubCFactory()
        self.hub_value_date = self.hub.get_hub_value_date()
        me_factories.SatC1Factory(hub_entity=self.hub, field_c1_str="static")

    def _dated_hub_value_date(self, value_date: str):
        hub_value_date = me_factories.CHubValueDateFactory(
            hub=self.hub, value_date=value_date
        )
        me_factories.SatTSC3Factory(
            hub_value_date=hub_value_date, field_tsc3_str="dated"
        )
        return hub_value_date

    def test_returns_the_row_of_the_hub_for_its_own_pk(self):
        obj = HubCManager().get_object_from_pk(self.hub_value_date.pk)

        self.assertEqual(obj.hub_id, self.hub.pk)
        self.assertEqual(obj.field_c1_str, "static")

    def test_resolves_a_pk_that_is_not_among_the_returned_rows(self):
        """The null-date pk still resolves once a dated row supersedes it."""
        dated = self._dated_hub_value_date("2026-06-30")
        returned_pks = {row.pk for row in HubCManager().repository.receive()}
        self.assertNotIn(self.hub_value_date.pk, returned_pks)

        obj = HubCManager().get_object_from_pk(self.hub_value_date.pk)

        self.assertEqual(obj.pk, dated.pk)
        self.assertEqual(obj.hub_id, self.hub.pk)

    def test_object_as_dict_uses_the_same_resolution(self):
        self._dated_hub_value_date("2026-06-30")

        as_dict = HubCManager().get_object_from_pk_as_dict(self.hub_value_date.pk)

        self.assertEqual(as_dict["field_tsc3_str"], "dated")

    def test_unknown_pk_raises_does_not_exist(self):
        with self.assertRaises(me_models.CHubValueDate.DoesNotExist):
            HubCManager().get_object_from_pk(self.hub_value_date.pk + 10_000)


class TestMontrekRepositoryHubValueDateHelpers(TestCase):
    def setUp(self):
        self.hub_value_date = me_factories.HubCFactory().get_hub_value_date()

    def test_get_hub_value_date_model_returns_the_hubs_value_date_model(self):
        self.assertIs(
            me_models.HubC.get_hub_value_date_model(), me_models.CHubValueDate
        )

    def test_get_hub_value_date_object_returns_the_instance(self):
        obj = HubCRepository().get_hub_value_date_object(self.hub_value_date.pk)

        self.assertEqual(obj, self.hub_value_date)
        self.assertIsInstance(obj, me_models.CHubValueDate)
