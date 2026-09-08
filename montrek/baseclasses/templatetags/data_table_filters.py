from django import template

from baseclasses.forms import FilterForm

register = template.Library()


@register.filter(name="add_class")
def add_class(field, css):
    return field.as_widget(attrs={"class": css})


@register.simple_tag(name="filter_caption")
def filter_caption(name: str) -> str:
    """Caption of the filter form in the language configured via LANGUAGE_CODE.

    ``name`` is the lowercased member name of ``FilterForm.Captions``; an unknown
    name renders as an empty string rather than breaking the page.
    """
    return FilterForm.Captions.texts.get(name, "")
