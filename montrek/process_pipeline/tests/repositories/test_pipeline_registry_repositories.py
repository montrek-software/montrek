import unittest

from process_pipeline.repositories.pipeline_registry_repositories import (
    PipelineRegistryRepositoryABC,
)
from process_pipeline.models.pipeline_registry_sat_models import (
    PipelineRegistrySatelliteABC,
)
from baseclasses.repositories.montrek_repository import MontrekRepository


class TestPipelineRegistryRepositoryABCStructure(unittest.TestCase):
    def test_inherits_montrek_repository(self):
        self.assertTrue(issubclass(PipelineRegistryRepositoryABC, MontrekRepository))

    def test_registry_satellite_annotation_is_declared(self):
        self.assertIn(
            "registry_satellite", PipelineRegistryRepositoryABC.__annotations__
        )

    def test_registry_fields_annotation_is_declared(self):
        self.assertIn("registry_fields", PipelineRegistryRepositoryABC.__annotations__)

    def test_default_order_fields(self):
        self.assertEqual(
            PipelineRegistryRepositoryABC.default_order_fields, ("-created_at",)
        )

    def test_set_annotations_is_defined(self):
        self.assertTrue(callable(PipelineRegistryRepositoryABC.set_annotations))

    def test_registry_satellite_type_annotation_wraps_correct_class(self):
        annotation = PipelineRegistryRepositoryABC.__annotations__["registry_satellite"]
        # type[X] is a GenericAlias — compare via __args__
        self.assertIn(PipelineRegistrySatelliteABC, annotation.__args__)

    def test_set_annotations_includes_celery_task_id(self):
        import inspect

        source = inspect.getsource(PipelineRegistryRepositoryABC.set_annotations)
        self.assertIn("celery_task_id", source)

    def test_set_annotations_includes_created_at(self):
        import inspect

        source = inspect.getsource(PipelineRegistryRepositoryABC.set_annotations)
        self.assertIn("created_at", source)
