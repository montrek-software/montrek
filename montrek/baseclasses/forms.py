from django import forms

class DateRangeForm(forms.Form):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date','id':'id_date_range_start'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'id':'id_date_range_end'}))

class MontrekCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        repository = kwargs.pop("repository",None)
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({"id": f"id_{field}"})

