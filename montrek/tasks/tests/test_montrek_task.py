from django.test import TestCase
from tasks.montrek_task import MontrekTask
from montrek.celery_app import app as celery_app


class MockMontrekTask(MontrekTask):
    ...


class TestMontrekTask(TestCase):
    def test_montrek_task__init(self):
        expected_task_name = f"{MockMontrekTask.__module__}.{MockMontrekTask.__name__}"
        MockMontrekTask()
        self.assertIn(expected_task_name, celery_app.tasks)
        registered_task = celery_app.tasks[expected_task_name]
        self.assertIsInstance(registered_task, MockMontrekTask)
        with self.assertRaises(ValueError) as e:
            MockMontrekTask(expected_task_name)
        self.assertEqual(
            str(e.exception),
            f"Task with name {expected_task_name} already registered. Please choose a different name.",
        )
