from django import forms
from baseclasses.forms import MontrekCreateForm
from montrek_example import models as me_models
from montrek_example.repositories.hub_a_repository import HubARepository


class ExampleACreateForm(MontrekCreateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["hubb_link"] = forms.ModelChoiceField(
            queryset=self.repository.get_hub_b_objects(),
            widget=forms.Select(attrs={"id": "id_hubb"}),
        )


