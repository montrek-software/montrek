from django import forms

class DateRangeForm(forms.Form):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date','id':'id_date_range_start'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'id':'id_date_range_end'}))

class MontrekCreateForm(forms.ModelForm):
    class Meta:
        exclude = ()

    def __init__(self, *args, **kwargs):
        self.repository = kwargs.pop("repository",None)
        self._meta.model = self.repository.hub_class
        super().__init__(*args, **kwargs)

        fields = self.repository.std_satellite_fields()
        for field in fields:
            form_field = field.formfield()
            if form_field:
                self.fields[field.name] = form_field
                self.fields[field.name].widget.attrs.update({"id": f"id_{field.name}"})

    def add_link_choice_field(self, field_name, queryset, required=False):
        self.fields[field_name] = MontrekModelChoiceField(
            queryset=queryset,
            widget=forms.Select(attrs={"id": f"id_{field_name}"}),
            required=required,
        )

class MontrekModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.field_b1_str
