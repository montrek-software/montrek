from django import template
from django.forms.widgets import CheckboxSelectMultiple

register = template.Library()


@register.filter
def is_checkbox_select_multiple(field):
    return isinstance(field.field.widget, CheckboxSelectMultiple)
