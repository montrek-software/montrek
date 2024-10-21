from dataclasses import dataclass
from django.test import TestCase

from baseclasses.errors.montrek_user_error import MontrekError
from baseclasses.repositories.montrek_repository import MontrekRepository
from file_upload.managers.import_processor_mixin import ImportProcessorMixin


@dataclass
class FakeHub:
    id: int
    fake_db_field: str | None


class FakeRepository(MontrekRepository):
    def std_queryset(self):
        return [
            FakeHub(1, "a"),
            FakeHub(2, "b"),
            FakeHub(3, "c"),
            FakeHub(4, "c"),
            FakeHub(5, ""),
            FakeHub(6, None),
        ]


class TestImportProcessorMixin(TestCase):
    def test_get_hubs_for_values(self):
        values = ["a", "b", "c", "d", "e"]
        actual = ImportProcessorMixin.get_hubs_for_values(
            values=values,
            repository=FakeRepository,
            repository_field="fake_db_field",
            raise_for_multiple_hubs=False,
            raise_for_unmapped_values=False,
        )
        actual_ids = [hub.id if hub else None for hub in actual]
        expected_ids = [1, 2, 4, None, None]
        self.assertEqual(actual_ids, expected_ids)

    def test_get_hubs_for_values_raises_error_for_multiple_hubs(self):
        values = ["a", "b", "c", "d", "e"]
        with self.assertRaisesMessage(
            MontrekError, "Multiple hubs found for values (truncated): c"
        ):
            ImportProcessorMixin.get_hubs_for_values(
                values=values,
                repository=FakeRepository,
                repository_field="fake_db_field",
                raise_for_multiple_hubs=True,
                raise_for_unmapped_values=False,
            )

    def test_get_hubs_for_values_raises_error_for_unmapped_values(self):
        values = ["a", "b", "c", "d", "e"]
        with self.assertRaisesMessage(
            MontrekError, "Cannot find hub for values (truncated): d, e"
        ):
            ImportProcessorMixin.get_hubs_for_values(
                values=values,
                repository=FakeRepository,
                repository_field="fake_db_field",
                raise_for_multiple_hubs=False,
                raise_for_unmapped_values=True,
            )
