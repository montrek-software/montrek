from django import forms
from .models import TransactionSatellite

class TransactionSatelliteForm(forms.ModelForm):
    class Meta:
        model = TransactionSatellite
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(TransactionSatelliteForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.disabled = True


