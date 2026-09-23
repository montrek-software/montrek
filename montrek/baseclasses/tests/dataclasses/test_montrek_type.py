from dataclasses import FrozenInstanceError

from baseclasses.dataclasses.montrek_type import MontrekType, MontrekTypeEnum
from django.test import TestCase
from reporting.core.reporting_colors import ReportingColors


class DummyTypes(MontrekTypeEnum):
    ALPHA = MontrekType(name="Alpha", color=ReportingColors.RED)
    BETA = MontrekType(name="Beta")


class TestMontrekTypeEnum(TestCase):
    def test_to_list(self):
        self.assertEqual(DummyTypes.to_list(), [("Alpha", "Alpha"), ("Beta", "Beta")])

    def test_to_color_dict(self):
        self.assertEqual(
            DummyTypes.to_color_dict(),
            {"Alpha": ReportingColors.RED, "Beta": ReportingColors.BLUE},
        )

    def test_from_name(self):
        self.assertIs(DummyTypes.from_name("Beta"), DummyTypes.BETA)

    def test_from_name__invalid_name(self):
        with self.assertRaises(ValueError):
            DummyTypes.from_name("Gamma")

    def test_montrek_type_is_frozen(self):
        with self.assertRaises(FrozenInstanceError):
            DummyTypes.ALPHA.value.color = ReportingColors.BLUE

    def test_duplicate_names_raise(self):
        with self.assertRaisesMessage(ValueError, "duplicate type names: Alpha"):

            class DuplicateTypes(MontrekTypeEnum):
                ALPHA = MontrekType(name="Alpha", color=ReportingColors.RED)
                OTHER_ALPHA = MontrekType(name="Alpha")

    def test_identical_values_raise(self):
        with self.assertRaisesMessage(ValueError, "duplicate type names: Alpha"):

            class AliasTypes(MontrekTypeEnum):
                ALPHA = MontrekType(name="Alpha")
                SAME_ALPHA = MontrekType(name="Alpha")
