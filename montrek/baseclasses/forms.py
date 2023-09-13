from django import forms

class DateRangeForm(forms.Form):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date','id':'id_date_range_start'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'id':'id_date_range_end'}))
