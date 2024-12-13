from django.test import TestCase
from tasks.montrek_task import MontrekTask
from montrek.celery_app import app as celery_app


class MockMontrekTask(MontrekTask):
    ...


class TestMontrekTask(TestCase):
    def test_montrek_task(self):
        task_name = f"{MockMontrekTask.__module__}.{MockMontrekTask.__name__}"
        self.assertIn(task_name, celery_app.tasks)
