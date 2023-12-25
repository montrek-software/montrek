from django import forms
from django.db.models import QuerySet


class DateRangeForm(forms.Form):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "id": "id_date_range_start"})
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "id": "id_date_range_end"})
    )


class MontrekCreateForm(forms.ModelForm):
    class Meta:
        exclude = ()

    def __init__(self, *args, **kwargs):
        self.repository = kwargs.pop("repository", None)
        self._meta.model = self.repository.hub_class
        super().__init__(*args, **kwargs)

        fields = self.repository.std_satellite_fields()
        for field in fields:
            form_field = field.formfield()
            if form_field:
                self.fields[field.name] = form_field
                self.fields[field.name].widget.attrs.update({"id": f"id_{field.name}"})

    def add_link_choice_field(
        self,
        link_name: str,
        queryset: QuerySet,
        display_field: str,
        required: bool = False,
    ):
        self.fields[link_name] = MontrekModelChoiceField(
            display_field=display_field,
            queryset=queryset,
            widget=forms.Select(attrs={"id": f"id_{link_name}"}),
            required=required,
        )


class MontrekModelChoiceField(forms.ModelChoiceField):
    def __init__(self, display_field: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.display_field = display_field

    def label_from_instance(self, obj):
        return getattr(obj, self.display_field)
