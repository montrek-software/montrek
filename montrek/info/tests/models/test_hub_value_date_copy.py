from baseclasses.repositories.db.hub_value_date_copy import HubValueDateCopy
from django.test import TestCase

from info.models.test_models import TestHubValueDateA


class TestHubValueDateCopyModels(TestCase):
    def test_leaves_out_unmanaged_models(self):
        self.assertNotIn(TestHubValueDateA, HubValueDateCopy(["info"]).models)
