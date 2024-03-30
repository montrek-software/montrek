import pandas as pd
from django.test import TestCase

from file_upload.tests.factories.field_map_factories import (
    FieldMapStaticSatelliteFactory,
)
from file_upload.managers.field_mapper import FieldMapper


class TestFieldMapper(TestCase):
    def test_apply_field_maps(self):
        FieldMapStaticSatelliteFactory()
        FieldMapStaticSatelliteFactory()

        source_df = pd.DataFrame(
            {"source_field_0": [1, 2, 3], "source_field_1": ["a", "b", "c"]}
        )

        field_mapper = FieldMapper(source_df)
        mapped_df = field_mapper.apply_field_maps()

        self.assertEqual(
            mapped_df.columns.to_list(), ["database_field_0", "database_field_1"]
        )
