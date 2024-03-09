from django import forms
from django.db.models import QuerySet


class DateRangeForm(forms.Form):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "id": "id_date_range_start"})
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "id": "id_date_range_end"})
    )


class FilterForm(forms.Form):
    filter_field = forms.CharField(
        widget=forms.TextInput(attrs={"id": "id_filter"}), required=False
    )
    filter_value = forms.CharField(
        widget=forms.TextInput(attrs={"id": "id_value"}), required=False
    )


class MontrekCreateForm(forms.ModelForm):
    class Meta:
        exclude = ()

    def __init__(self, *args, **kwargs):
        self.repository = kwargs.pop("repository", None)
        self._meta.model = self.repository.hub_class
        super().__init__(*args, **kwargs)

        self._add_satellite_fields()
        self._add_hub_entity_id_field()

    def _add_satellite_fields(self):
        fields = self.repository.std_satellite_fields()
        for field in fields:
            form_field = field.formfield()
            if form_field and field.name not in self._meta.exclude:
                self.fields[field.name] = form_field
                self.fields[field.name].widget.attrs.update({"id": f"id_{field.name}"})
        self.fields["comment"] = forms.CharField()

    def _add_hub_entity_id_field(self):
        self.fields["hub_entity_id"] = forms.IntegerField(required=False)
        self.fields["hub_entity_id"].widget.attrs.update({"id": "id_hub_entity_id"})
        self.fields["hub_entity_id"].widget.attrs.update({"readonly": True})

    def add_link_choice_field(
        self,
        link_name: str,
        queryset: QuerySet,
        display_field: str,
        required: bool = False,
        **kwargs,
    ):
        self.fields[link_name] = MontrekModelChoiceField(
            display_field=display_field,
            queryset=queryset,
            widget=forms.Select(attrs={"id": f"id_{link_name}"}),
            required=required,
            **kwargs,
        )


class MontrekModelChoiceField(forms.ModelChoiceField):
    def __init__(self, display_field: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.display_field = display_field

    def label_from_instance(self, obj):
        return getattr(obj, self.display_field)
