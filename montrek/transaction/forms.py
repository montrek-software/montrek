from django import forms
from .models import TransactionSatellite
from .models import TransactionCategoryMapSatellite

class TransactionSatelliteForm(forms.ModelForm):
    class Meta:
        model = TransactionSatellite
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.disabled = True


class TransactionCategoryMapSatelliteForm(forms.ModelForm):
    class Meta:
        model = TransactionCategoryMapSatellite
        fields = ('field', 'value', 'category')
