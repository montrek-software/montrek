from baseclasses.forms import MontrekCreateForm
from montrek_example import models as me_models

class SatelliteA1CreateForm(MontrekCreateForm):
    class Meta:
        model = me_models.SatA1 
        fields = (
            "field_a1_str",
            "field_a1_int",
        )

class SatelliteA2CreateForm(MontrekCreateForm):
    class Meta:
        model = me_models.SatA2
        fields = (
            "field_a2_str",
            "field_a2_float",
        )
