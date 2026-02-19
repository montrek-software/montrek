from typing import Any

from baseclasses.models import LinkTypeEnum
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.db.models import DateField, QuerySet, TextChoices
from django.forms.widgets import ChoiceWidget
from encrypted_fields import EncryptedCharField


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
        EQUALS = "exact", "equals (case-sensitive)"
        I_EQUALS = "iexact", "equals"
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
        filter_index: int = 0,
        *args,
        **kwargs,
    ):
        # Set default values
        filter_field = ""
        filter_lookup = "iexact"
        filter_negate = False
        filter_value = ""

        if not filter or not isinstance(filter, dict):
            self.set_filter_fields(
                filter_field,
                filter_field_choices,
                filter_negate,
                filter_lookup,
                filter_value,
                *args,
                **kwargs,
            )
            return

        filter_items = list(filter.items())
        if filter_index >= len(filter_items):
            self.set_filter_fields(
                filter_field,
                filter_field_choices,
                filter_negate,
                filter_lookup,
                filter_value,
                *args,
                **kwargs,
            )
            return

        filter_key, value = filter_items[filter_index]

        if filter_key.upper() == "OR":
            self.set_filter_fields(
                filter_field,
                filter_field_choices,
                filter_negate,
                filter_lookup,
                filter_value,
                *args,
                **kwargs,
            )
            return

        try:
            filter_field, filter_lookup = filter_key.split("__", 1)
        except ValueError:
            filter_field = filter_key
            filter_lookup = "exact"

        filter_negate = value.get("filter_negate", False)
        filter_value = value.get("filter_value", "")
        if isinstance(filter_value, list):
            filter_value = ",".join(map(str, filter_value))

        # Set filter values as instance attributes
        filter_field_choices = filter_field_choices or []
        self.set_filter_fields(
            filter_field,
            filter_field_choices,
            filter_negate,
            filter_lookup,
            filter_value,
            *args,
            **kwargs,
        )

    def set_filter_fields(
        self,
        filter_field,
        filter_field_choices,
        filter_negate,
        filter_lookup,
        filter_value,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.fields["filter_field"] = forms.ChoiceField(
            initial=filter_field,
            choices=filter_field_choices,
            widget=forms.Select(attrs={"id": "id_field", "class": "form-control"}),
            required=False,
        )
        self.fields["filter_negate"] = forms.ChoiceField(
            initial=filter_negate,
            choices=[
                (False, ""),
                (True, "not"),
            ],
            required=False,
            widget=forms.Select(attrs={"id": "id_negate", "class": "form-control"}),
        )
        self.fields["filter_lookup"] = forms.ChoiceField(
            initial=filter_lookup,
            choices=self.LookupChoices,
            widget=forms.Select(attrs={"id": "id_lookup", "class": "form-control"}),
            required=False,
        )
        self.fields["filter_value"] = forms.CharField(
            initial=filter_value,
            widget=forms.TextInput(attrs={"id": "id_value", "class": "form-control"}),
            required=False,
        )


class MontrekCreateForm(forms.ModelForm):
    class Meta:
        exclude = ("comment",)

    def __init__(self, *args, **kwargs):
        self.repository = kwargs.pop("repository", None)
        if not self.repository:
            raise ValueError("Repository required")

        from copy import deepcopy

        self._meta = deepcopy(self._meta)
        self._meta.model = self.repository.hub_class

        self.session_data = kwargs.pop("session_data", {})
        self.satellite_fields = self.repository.std_satellite_fields()

        super().__init__(*args, **kwargs)

        self._add_satellite_fields()
        self._add_hub_entity_id_field()
        self._apply_bootstrap_classes()

    # -------------------------
    # Field Creation
    # -------------------------

    def _add_satellite_fields(self):
        exclude = set(self._meta.exclude or ())

        for field in self.satellite_fields:
            form_field = self._get_form_field(field)
            if not form_field or field.name in exclude:
                continue

            form_field.validators.extend(field.validators)

            if field.name in self.repository.display_field_names:
                form_field.label = self.repository.display_field_names[field.name]

            self.fields[field.name] = form_field

    def _get_form_field(self, field):
        if isinstance(field, EncryptedCharField):
            # TODO: This is not safe, as the value can be stolen! Set render_value to False, but make sure montrek behaviour still works!
            return field.formfield(widget=forms.PasswordInput(render_value=True))

        if isinstance(field, DateField):
            return field.formfield(widget=forms.DateInput(attrs={"type": "date"}))

        return field.formfield()

    def _add_hub_entity_id_field(self):
        self.fields["hub_entity_id"] = forms.IntegerField(required=False)
        self.fields["hub_entity_id"].widget.attrs.update({"readonly": True})

    # -------------------------
    # Bootstrap Styling
    # -------------------------

    def _apply_bootstrap_classes(self):
        for name, field in self.fields.items():
            widget = field.widget

            # Checkbox
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = "form-check-input"

            # Select
            elif isinstance(widget, forms.Select):
                widget.attrs["class"] = "form-select"

            # Textarea
            elif isinstance(widget, forms.Textarea):
                widget.attrs["class"] = "form-control resizable"

            # Date input
            elif isinstance(widget, forms.DateInput):
                widget.attrs["class"] = "form-control w-auto"

            # Default text-like inputs
            else:
                widget.attrs["class"] = "form-control"

            widget.attrs["id"] = f"id_{name}"

            # Readonly styling
            if widget.attrs.get("readonly"):
                existing_class = widget.attrs.get("class", "")
                if existing_class:
                    widget.attrs["class"] = f"{existing_class} form-control-plaintext"
                else:
                    widget.attrs["class"] = "form-control-plaintext"

    def set_field_order(self):
        """
        Ensure 'hub_entity_id' is ordered last without mutating any class-level
        field_order list in-place.
        """
        if self.field_order:
            # Work on a copy so we don't mutate a potentially shared class attribute.
            field_order = list(self.field_order)
        else:
            field_order = [field for field in self.fields if field != "hub_entity_id"]

        if "hub_entity_id" not in field_order:
            field_order.append("hub_entity_id")

        # Store on the instance so it no longer relies on a class-level list.
        self.field_order = field_order
        self.order_fields(field_order)

    def add_link_choice_field(
        self,
        link_name: str,
        queryset: QuerySet,
        display_field: str,
        required: bool = False,
        is_char_field: bool = False,
        use_checkboxes_for_many_to_many: bool = True,
        separator: str = ";",
        readonly: bool = False,
        **kwargs,
    ):
        link_class = getattr(self.repository.hub_class, link_name).through
        is_many_to_many = link_class.link_type == LinkTypeEnum.MANY_TO_MANY

        if is_many_to_many:
            choice_class = MontrekModelMultipleChoiceField
            kwargs["use_checkboxes_for_many_to_many"] = use_checkboxes_for_many_to_many
        elif is_char_field:
            choice_class = MontrekModelCharChoiceField
        else:
            choice_class = MontrekModelChoiceField

        initial_link = choice_class.get_initial_link(
            self.initial, queryset, display_field, separator
        )
        if readonly:
            kwargs["widget"] = forms.TextInput(attrs={"readonly": "readonly"})
        form_field = choice_class(
            display_field=display_field,
            queryset=queryset,
            required=required,
            initial=initial_link,
            **kwargs,
        )
        if link_name in self.repository.display_field_names:
            form_field.label = self.repository.display_field_names[link_name]
        self.fields[link_name] = form_field


class BaseMontrekChoiceField:
    def __init__(self, display_field: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.display_field = display_field
        # Ensure Bootstrap styling
        css_class = self.widget.attrs.get("class", "")
        self.widget.attrs["class"] = f"{css_class} form-select".strip()

    def label_from_instance(self, obj):
        return getattr(obj, self.display_field)

    @staticmethod
    def get_initial_link(
        initial: dict[str, Any], queryset: QuerySet, display_field: str, separator: str
    ) -> object | None:
        raise NotImplementedError("Subclasses must implement this method.")


class MontrekModelChoiceField(BaseMontrekChoiceField, forms.ModelChoiceField):
    @staticmethod
    def get_initial_link(
        initial: dict[str, Any], queryset: QuerySet, display_field: str, separator: str
    ) -> object | None:
        initial_link = queryset.filter(
            **{display_field: initial.get(display_field)}
        ).first()
        return initial_link


class MontrekModelMultipleChoiceField(
    BaseMontrekChoiceField, forms.ModelMultipleChoiceField
):
    def __init__(
        self,
        display_field: str,
        use_checkboxes_for_many_to_many: bool = True,
        *args,
        **kwargs,
    ):
        kwargs["widget"] = self.get_widget(
            display_field, use_checkboxes_for_many_to_many
        )
        super().__init__(display_field, *args, **kwargs)

    @staticmethod
    def get_widget(display_field, use_checkboxes: bool) -> ChoiceWidget:
        if use_checkboxes:
            return forms.CheckboxSelectMultiple()
        return FilteredSelectMultiple(verbose_name=display_field, is_stacked=False)

    @staticmethod
    def get_initial_link(
        initial: dict[str, Any], queryset: QuerySet, display_field: str, separator: str
    ) -> object | None | QuerySet:
        initial_links_str = initial.get(display_field)
        if not isinstance(initial_links_str, str):
            return None
        filter_kwargs = {f"{display_field}__in": initial_links_str.split(separator)}
        return queryset.filter(**filter_kwargs).all()


class MontrekModelCharChoiceField(BaseMontrekChoiceField, forms.CharField):
    def __init__(self, display_field, *args, **kwargs):
        self.queryset = kwargs.pop("queryset", QuerySet())
        super().__init__(display_field, *args, **kwargs)

    @staticmethod
    def get_initial_link(
        initial: dict[str, Any], queryset: QuerySet, display_field: str, separator: str
    ) -> object | None:
        return initial.get(display_field)

    def clean(self, value):
        if not value:
            if self.required:
                raise forms.ValidationError("No value given")
            return None
        instance = self.queryset.filter(**{self.display_field: value})
        if not instance:
            raise forms.ValidationError("No matching object found!")
        if instance.count() == 1:
            return instance.get()
        raise forms.ValidationError("Multiple matching objects found!")
