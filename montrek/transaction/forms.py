from django import forms
from .models import TransactionSatellite

class TransactionSatelliteForm(forms.ModelForm):
    class Meta:
        model = TransactionSatellite
        fields = '__all__'

