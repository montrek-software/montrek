from django.db.models import CASCADE, DecimalField, ForeignKey


class HubForeignKey(ForeignKey):
    def __init__(self, *args, **kwargs):
        on_delete = kwargs.pop("on_delete", CASCADE)
        related_name = kwargs.pop("related_name", "hub_value_date")
        super().__init__(
            *args, on_delete=on_delete, related_name=related_name, **kwargs
        )


class FractionField(DecimalField):
    """Percentage stored as a fraction (0.05 for 5%).

    Forms show and take percent values (5 for 5%) through
    ``PercentDecimalFormField``; tables show it with ``PercentTableElement``.
    Six decimal places keep four decimals of the percent value.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_digits", 9)
        kwargs.setdefault("decimal_places", 6)
        kwargs.setdefault("null", True)
        kwargs.setdefault("blank", True)
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        # Imported here: baseclasses.forms imports the models, which import
        # this module.
        from baseclasses.forms import PercentDecimalFormField

        # Overrides the German decimal field montrek forms pass for
        # DE formatting; the percent field parses decimal commas itself.
        kwargs["form_class"] = PercentDecimalFormField
        return super().formfield(**kwargs)
