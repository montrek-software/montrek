from baseclasses.forms import MontrekCreateForm
from montrek_example import models as me_models

class HubACreateForm(MontrekCreateForm):
    class Meta:
        model = me_models.SatA1
        fields = (
            "field_a1_str",
            "field_a1_int",
        )
