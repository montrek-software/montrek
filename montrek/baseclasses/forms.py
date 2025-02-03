from django.contrib.admin.widgets import FilteredSelectMultiple
from typing import Any
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


class FilterForm(forms.Form):
    class LookupChoices(TextChoices):
        CONTAINS = "contains", "contains"
        ENDS_WITH = "endswith", "ends with"
        # With MariaDB collation utf9mb4_general_ci 'exact' is case-insensitive.
        EQUALS = "exact", "equals"
        GREATER_THAN = "gt", ">"
        GREATER_THAN_OR_EQUAL = "gte", ">="
        IN = "in", "in"
        IS_NULL = "isnull", "is null"
        LESS_THAN = "lt", "<"
        LESS_THAN_OR_EQUAL = "lte", "<="
        STARTS_WITH = "startswith", "starts with"

    def __init__(
        self,
        filter_field_choices: list[tuple] | None = None,
        filter: dict | None = None,
        *args,
        **kwargs,
    ):
        if filter and isinstance(filter, dict):
            filter_key, value = list(filter.items())[0]
            if filter_key.upper() == "OR":
                filter_field = ""
                filter_lookup = "exact"
                filter_negate = False
                filter_value = ""
            else:
                filter_field, filter_lookup = filter_key.split("__")
                filter_negate = value["filter_negate"]
                filter_value = value["filter_value"]
                if isinstance(filter_value, list):
                    filter_value = ",".join(filter_value)
        else:
            filter_field = ""
            filter_lookup = "exact"
            filter_negate = False
            filter_value = ""
        filter_field_choices = filter_field_choices or []
        super().__init__(*args, **kwargs)

        self.fields["filter_field"] = forms.ChoiceField(
            initial=filter_field,
            choices=filter_field_choices,
            widget=forms.Select(attrs={"id": "id_field"}),
            required=False,
        )
        self.fields["filter_negate"] = forms.ChoiceField(
            initial=filter_negate,
            choices=[
                (False, ""),
                (True, "not"),
            ],
            required=False,
            widget=forms.Select(attrs={"id": "id_negate"}),
        )
        self.fields["filter_lookup"] = forms.ChoiceField(
            initial=filter_lookup,
            choices=self.LookupChoices,
            widget=forms.Select(attrs={"id": "id_lookup"}),
            required=False,
        )
        self.fields["filter_value"] = forms.CharField(
            initial=filter_value,
            widget=forms.TextInput(attrs={"id": "id_value"}),
            required=False,
        )


class MontrekCreateForm(forms.ModelForm):
    class Meta:
        exclude = ()

    def __init__(self, *args, **kwargs):
        self.repository = kwargs.pop("repository", None)
        if self.repository:
            self._meta.model = self.repository.hub_class
        super().__init__(*args, **kwargs)
        self.initial = kwargs.get("initial", {})

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
        initial_link = choice_class.get_initial_link(
            self.initial, queryset, display_field
        )
        self.fields[link_name] = choice_class(
            display_field=display_field,
            queryset=queryset,
            required=required,
            initial=initial_link,
            **kwargs,
        )


class BaseMontrekChoiceField:
    def __init__(self, display_field: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.display_field = display_field

    def label_from_instance(self, obj):
        return getattr(obj, self.display_field)

    @staticmethod
    def get_initial_link(
        initial: dict[str, Any], queryset: QuerySet, display_field: str
    ) -> object | None:
        raise NotImplementedError("Subclasses must implement this method.")


class MontrekModelChoiceField(BaseMontrekChoiceField, forms.ModelChoiceField):
    @staticmethod
    def get_initial_link(
        initial: dict[str, Any], queryset: QuerySet, display_field: str
    ) -> object | None:
        initial_link = queryset.filter(
            **{display_field: initial.get(display_field)}
        ).first()
        return initial_link


class MontrekModelMultipleChoiceField(
    BaseMontrekChoiceField, forms.ModelMultipleChoiceField
):
    def __init__(self, display_field: str, *args, **kwargs):
        use_checkboxes_for_many_to_many = kwargs.pop(
            "use_checkboxes_for_many_to_many", True
        )
        if use_checkboxes_for_many_to_many:
            kwargs["widget"] = forms.CheckboxSelectMultiple()
        else:
            kwargs["widget"] = FilteredSelectMultiple(
                verbose_name="display_field", is_stacked=False
            )
        super().__init__(display_field, *args, **kwargs)

    @staticmethod
    def get_initial_link(
        initial: dict[str, Any], queryset: QuerySet, display_field: str
    ) -> object | None | QuerySet:
        initial_links_str = initial.get(display_field)
        if not isinstance(initial_links_str, str):
            return None
        filter_kwargs = {f"{display_field}__in": initial_links_str.split(",")}
        return queryset.filter(**filter_kwargs).all()
