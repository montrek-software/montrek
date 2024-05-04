from django.db.models import TextChoices
from django import forms
from django.db.models import QuerySet

from baseclasses.models import LinkTypeEnum


class DateRangeForm(forms.Form):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "id": "id_date_range_start"})
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "id": "id_date_range_end"})
    )


# todo: find a better place for this
class FilterOperatorChoices(TextChoices):
    IN = '__in', 'in'

class FilterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.filter_field_choices = kwargs.pop("filter_field_choices", [])
        super().__init__(*args, **kwargs)

        self.fields['filter_field'] = forms.ChoiceField(
            choices=self.filter_field_choices, widget=forms.Select(attrs={"id": "id_field"}), 
            required=False
        )
        self.fields['filter_operator'] = forms.ChoiceField(
            choices=FilterOperatorChoices, widget=forms.Select(attrs={"id": "id_field"}), 
            required=False
        )
        self.fields['filter_value'] = forms.CharField(
            widget=forms.TextInput(attrs={"id": "id_value"}), required=False
        )


class MontrekCreateForm(forms.ModelForm):
    class Meta:
        exclude = ()

    def __init__(self, *args, **kwargs):
        self.repository = kwargs.pop("repository", None)
        if self.repository:
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
        link_class = getattr(self.repository.hub_class, link_name).through
        is_many_to_many = link_class.link_type == LinkTypeEnum.MANY_TO_MANY

        choice_class = (
            MontrekModelMultipleChoiceField
            if is_many_to_many
            else MontrekModelChoiceField
        )
        self.fields[link_name] = choice_class(
            display_field=display_field,
            queryset=queryset,
            required=required,
            **kwargs,
        )


class BaseMontrekChoiceField:
    def __init__(self, display_field: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.display_field = display_field

    def label_from_instance(self, obj):
        return getattr(obj, self.display_field)


class MontrekModelChoiceField(BaseMontrekChoiceField, forms.ModelChoiceField):
    pass


class MontrekModelMultipleChoiceField(
    BaseMontrekChoiceField, forms.ModelMultipleChoiceField
):
    def __init__(self, display_field: str, *args, **kwargs):
        kwargs["widget"] = forms.CheckboxSelectMultiple()
        super().__init__(display_field, *args, **kwargs)
