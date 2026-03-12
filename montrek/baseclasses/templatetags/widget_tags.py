from django import template

register = template.Library()


@register.filter
def is_checkbox_select_multiple(field):
    from django.forms.widgets import CheckboxSelectMultiple

    return isinstance(field.field.widget, CheckboxSelectMultiple)
