from django import forms


class UploadFileForm(forms.Form):
    file = forms.FileField(
        widget=forms.FileInput(
            attrs={
                "id": "id_dkb_transactions_upload__file",
                "class": "form-control-file",
                "accept": ".csv",
            }
        )
    )
