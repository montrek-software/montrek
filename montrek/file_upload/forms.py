import inspect
from django import forms
from django.forms.fields import ChoiceField

from baseclasses.forms import MontrekCreateForm


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
            ),
        )


class SimpleUploadFileForm(UploadFileForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["overwrite"] = forms.BooleanField(
            required=False,
            label="Overwrite existing data",
            widget=forms.CheckboxInput(
                attrs={
                    "id": "id_upload__overwrite",
                    "class": "form-check-input",
                }
            ),
        )


class FieldMapCreateForm(MontrekCreateForm):
    def __init__(self, *args, **kwargs):
        self.field_map_manager = kwargs.pop("field_map_manager")
        super().__init__(*args, **kwargs)
        self.fields["function_name"] = ChoiceField(
            choices=[(f, f) for f in self._get_function_name_choices()],
        )
        if "function_name" not in self.initial.keys():
            self.initial["function_name"] = "no_change"

    def _get_function_name_choices(self):
        function_names = []
        for name, _ in inspect.getmembers(
            self.field_map_manager.field_map_function_manager_class, inspect.isfunction
        ):
            function_names.append(name)
        return sorted(list(set(function_names)))
