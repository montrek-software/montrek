from django.test import TestCase

from data_import.testing.models import TestRegistryHub, TestRegistrySatellite


class TestCeleryTaskIdOnConcreteModel(TestCase):
    """
    Verifies celery_task_id of the pipeline registry satellite is inherited
    correctly by a concrete subclass.
    """

    def test_celery_task_id_default_on_concrete_model(self):
        hub = TestRegistryHub.objects.create()
        sat = TestRegistrySatellite.objects.create(hub_entity=hub)
        self.assertEqual(sat.celery_task_id, "")

    def test_celery_task_id_can_be_written_and_read(self):
        hub = TestRegistryHub.objects.create()
        sat = TestRegistrySatellite.objects.create(
            hub_entity=hub, celery_task_id="task-xyz"
        )
        sat.refresh_from_db()
        self.assertEqual(sat.celery_task_id, "task-xyz")
