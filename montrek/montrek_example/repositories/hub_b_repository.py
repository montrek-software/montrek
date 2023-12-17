from montrek_example import models as me_models
from baseclasses.repositories.montrek_repository import MontrekRepository

class HubBRepository(MontrekRepository):
    hub_class = me_models.HubB

    def test_queryset_1(self):
        self.add_linked_satellites_field_annotations(
            me_models.SatA1,
            me_models.LinkHubAHubB,
            ['field_a1_int'],
            self.reference_date,
            reversed_link=True
        )
        return self.build_queryset()
