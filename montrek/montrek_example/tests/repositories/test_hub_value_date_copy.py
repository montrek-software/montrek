import datetime

from django.test import TestCase
from user.tests.factories.montrek_user_factories import MontrekUserFactory

from montrek_example.models import example_models as me_models
from montrek_example.repositories.hub_c_repository import HubCRepository

DATE = datetime.date(2024, 1, 15)


class TestValueDateCopyIsWritten(TestCase):
    def test_create_by_dict_copies_the_date(self):
        user = MontrekUserFactory()
        hub = HubCRepository({"user_id": user.pk}).create_by_dict(
            {"field_tsc2_float": 0.1, "value_date": DATE}
        )

        self.assertEqual(
            list(
                me_models.CHubValueDate.objects.filter(
                    hub=hub, value_date_list__value_date=DATE
                ).values_list("value_date_copy", flat=True)
            ),
            [DATE],
        )
