from django.test import TestCase

from baseclasses.models import TestMontrekSatellite
from baseclasses.repositories.db.satellite_hashes import (
    identifier_hash,
    recompute_hash_values,
    value_hash,
)
from baseclasses.tests.factories.baseclass_factories import (
    TestMontrekSatelliteFactory,
)

IDENTIFIER_FIELDS = tuple(TestMontrekSatellite.identifier_fields)
VALUE_FIELDS = tuple(
    field
    for field in TestMontrekSatellite.get_value_field_names()
    if field not in TestMontrekSatellite.exclude_from_hash_value()
)


class TestSatelliteHashes(TestCase):
    def setUp(self):
        self.satellites = TestMontrekSatelliteFactory.create_batch(2)

    def test_hashes_match_satellite_hashes(self):
        for satellite in TestMontrekSatellite.objects.all():
            self.assertEqual(
                identifier_hash(satellite, IDENTIFIER_FIELDS),
                satellite.get_hash_identifier,
            )
            self.assertEqual(
                value_hash(satellite, VALUE_FIELDS), satellite.get_hash_value
            )

    def test_recompute_hash_values(self):
        TestMontrekSatellite.objects.update(hash_value="outdated")

        recompute_hash_values(TestMontrekSatellite, VALUE_FIELDS)

        for satellite in TestMontrekSatellite.objects.all():
            self.assertEqual(satellite.hash_value, satellite.get_hash_value)
