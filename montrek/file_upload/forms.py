from django import forms
from django.forms.fields import ChoiceField

from baseclasses.forms import MontrekCreateForm
from baseclasses.models import MontrekSatelliteABC
from file_upload.managers.field_map_manager import FieldMapManager


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
        self.fields["function_name"] = ChoiceField(
            choices=[(f, f) for f in self._get_function_name_choices()],
        )
        self.initial["function_name"] = "fn_no_change"

    @classmethod
    def _get_database_field_choices(cls):
        satellite_classes = MontrekSatelliteABC.__subclasses__()
        value_fields = []
        for satellite_class in satellite_classes:
            value_fields += satellite_class.get_value_field_names()
        return sorted(list(set(value_fields)))

    @classmethod
    def _get_function_name_choices(cls):
        field_map_manager_classes = FieldMapManager.__subclasses__()
        function_names = []
        for field_map_manager_class in field_map_manager_classes:
            function_names += [
                f for f in dir(field_map_manager_class) if f.startswith("fn_")
            ]
        return sorted(list(set(function_names)))
