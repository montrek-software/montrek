from baseclasses.forms import MontrekCreateForm
from montrek_example import models as me_models

class HubACreateForm(MontrekCreateForm):
    class Meta:
        model = me_models.HubA
        fields = [
            "field_hub_a_str",
            "field_hub_a_int",
        ]
