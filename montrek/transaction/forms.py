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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['field'].widget.attrs.update({'id': 'id_transaction_category_new__field'})
        self.fields['value'].widget.attrs.update({'id': 'id_transaction_category_new__value'})
        self.fields['category'].widget.attrs.update({'id': 'id_transaction_category_new__category'})
