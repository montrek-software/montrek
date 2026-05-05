import unittest

from django.test import TestCase

from process_pipeline.models.pipeline_registry_hub_models import PipelineRegistryHubABC
from process_pipeline.models.pipeline_registry_sat_models import (
    PipelineRegistrySatelliteABC,
)
from baseclasses.models import MontrekHubABC, MontrekSatelliteABC


class TestPipelineRegistryHubABCStructure(unittest.TestCase):
    def test_is_abstract(self):
        self.assertTrue(PipelineRegistryHubABC._meta.abstract)

    def test_inherits_montrek_hub_abc(self):
        self.assertTrue(issubclass(PipelineRegistryHubABC, MontrekHubABC))


class TestPipelineRegistrySatelliteABCStructure(unittest.TestCase):
    def test_is_abstract(self):
        self.assertTrue(PipelineRegistrySatelliteABC._meta.abstract)

    def test_inherits_montrek_satellite_abc(self):
        self.assertTrue(issubclass(PipelineRegistrySatelliteABC, MontrekSatelliteABC))

    def test_celery_task_id_field_exists(self):
        field = PipelineRegistrySatelliteABC._meta.get_field("celery_task_id")
        self.assertIsNotNone(field)

    def test_celery_task_id_max_length(self):
        field = PipelineRegistrySatelliteABC._meta.get_field("celery_task_id")
        self.assertEqual(field.max_length, 255)

    def test_celery_task_id_default_is_empty_string(self):
        field = PipelineRegistrySatelliteABC._meta.get_field("celery_task_id")
        self.assertEqual(field.default, "")


class TestCeleryTaskIdOnConcreteModel(TestCase):
    """
    Verifies celery_task_id is inherited correctly by a concrete subclass.
    Uses data_import's TestRegistrySatellite which already has a DB table.
    """

    def test_celery_task_id_default_on_concrete_model(self):
        from data_import.base.models import TestRegistryHub, TestRegistrySatellite

        hub = TestRegistryHub.objects.create()
        sat = TestRegistrySatellite.objects.create(hub_entity=hub)
        self.assertEqual(sat.celery_task_id, "")

    def test_celery_task_id_can_be_written_and_read(self):
        from data_import.base.models import TestRegistryHub, TestRegistrySatellite

        hub = TestRegistryHub.objects.create()
        sat = TestRegistrySatellite.objects.create(
            hub_entity=hub, celery_task_id="task-xyz"
        )
        sat.refresh_from_db()
        self.assertEqual(sat.celery_task_id, "task-xyz")
