from django import forms

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
            )
        )


class FieldMapCreateForm(MontrekCreateForm):
    pass
