from django import forms
from django.forms.fields import ChoiceField

from baseclasses.forms import MontrekCreateForm
from baseclasses.models import MontrekSatelliteABC


class UploadFileForm(forms.Form):
    def __init__(self, accept: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.accept = accept
        self.fields["file"] = forms.FileField(
            widget=forms.FileInput(
                attrs={
                    "id": "id_upload__file",
                    "class": "form-control-file",
                    "accept": self.accept,
                }
            )
        )


class FieldMapCreateForm(MontrekCreateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["database_field"] = ChoiceField(
            choices=[(f, f) for f in self._get_database_field_choices()],
        )

    @classmethod
    def _get_database_field_choices(cls):
        satellite_classes = MontrekSatelliteABC.__subclasses__()
        value_fields = []
        for satellite_class in satellite_classes:
            value_fields += satellite_class.get_value_field_names()
        return sorted(list(set(value_fields)))
