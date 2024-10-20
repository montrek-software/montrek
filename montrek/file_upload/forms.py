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


class FieldMapCreateForm(MontrekCreateForm):
    def __init__(self, *args, **kwargs):
        self.field_map_manager = kwargs.pop("field_map_manager")
        self.related_manager = kwargs.pop("related_manager")
        super().__init__(*args, **kwargs)
        self.fields["database_field"] = ChoiceField(
            choices=[(f, f) for f in self._get_database_field_choices()],
        )
        self.fields["function_name"] = ChoiceField(
            choices=[(f, f) for f in self._get_function_name_choices()],
        )
        self.initial["function_name"] = "no_change"

    def _get_database_field_choices(self):
        field_names = self.related_manager.get_std_queryset_field_choices()
        return [field_name[0] for field_name in field_names]

    def _get_function_name_choices(self):
        function_names = []
        for name, _ in inspect.getmembers(
            self.field_map_manager.field_map_function_manager_class, inspect.isfunction
        ):
            function_names.append(name)
        return sorted(list(set(function_names)))
