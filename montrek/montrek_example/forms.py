from django import forms
from baseclasses.forms import MontrekCreateForm
from montrek_example import models as me_models


class SatelliteA1CreateForm(MontrekCreateForm):
    class Meta:
        model = me_models.SatA1
        fields = (
            "field_a1_str",
            "field_a1_int",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["hubb_link"] = forms.ModelChoiceField(
            queryset=me_models.HubB.objects.all(),
            widget=forms.Select(attrs={"id": "id_hubb"}),
        )


class SatelliteA2CreateForm(MontrekCreateForm):
    class Meta:
        model = me_models.SatA2
        fields = (
            "field_a2_str",
            "field_a2_float",
        )


class SatelliteB1CreateForm(MontrekCreateForm):
    class Meta:
        model = me_models.SatB1
        fields = (
            "field_b1_str",
            "field_b1_date",
        )


class SatelliteB2CreateForm(MontrekCreateForm):
    class Meta:
        model = me_models.SatB2
        fields = (
            "field_b2_str",
            "field_b2_choice",
        )
