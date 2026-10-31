from django.test import TestCase

from process_pipeline.constants import (
    RegistryStatusDataClass,
    RegistryStatusTextChoices,
)


class MockStatus(RegistryStatusTextChoices):
    PENDING = RegistryStatusDataClass("pending", is_active=True)
    RUNNING = RegistryStatusDataClass("running", is_active=True)
    DONE = RegistryStatusDataClass("done")


class TestRegistryStatusTextChoices(TestCase):
    def test_active_labels(self):
        self.assertEqual(MockStatus.active_labels(), ("pending", "running"))
