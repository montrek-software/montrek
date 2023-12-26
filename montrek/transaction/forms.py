from django import forms
from account.repositories.account_repository import AccountRepository
from baseclasses.forms import MontrekCreateForm
from .models import TransactionSatellite
from .models import TransactionCategoryMapSatellite
from transaction.repositories.transaction_category_repository import TransactionCategoryRepository

class TransactionCategoryMapSatelliteForm(forms.ModelForm):
    class Meta:
        model = TransactionCategoryMapSatellite
        fields = ('field', 'value', 'category', 'is_regex')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['field'].widget.attrs.update({'id': 'id_transaction_category_new__field'})
        self.fields['value'].widget.attrs.update({'id': 'id_transaction_category_new__value'})
        self.fields['category'].widget.attrs.update({'id': 'id_transaction_category_new__category'})
        self.fields['is_regex'].widget.attrs.update({'id': 'id_transaction_category_new__regex'})


class TransactionCreateForm(MontrekCreateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_link_choice_field(
            display_field="account_name",
            link_name="link_transaction_account",
            queryset=AccountRepository({}).std_queryset(),
        )
        self.add_link_choice_field(
            display_field="typename",
            link_name="link_transaction_transaction_category",
            queryset=TransactionCategoryRepository({}).std_queryset(),
        )
