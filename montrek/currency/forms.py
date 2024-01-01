from baseclasses.forms import MontrekCreateForm

class CurrencyCreateForm(MontrekCreateForm):
    class Meta():
        exclude = ['value_date', 'fx_rate']
