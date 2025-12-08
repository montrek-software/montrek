from django import template
from django.template.loader import get_template
from reporting.managers.montrek_table_manager import MontrekTableManagerABC

register = template.Library()


@register.simple_tag
def render_table(table_manager: MontrekTableManagerABC):
    template = get_template("tables/base_table.html")
    return template.render(context={"table_manager": table_manager})
