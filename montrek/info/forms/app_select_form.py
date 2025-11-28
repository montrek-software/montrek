import math
from collections import defaultdict

from django import forms
from django.apps import apps as django_apps
from reporting.forms import MontrekReportForm


def get_group_key(app_config):
    parts = app_config.name.split(".")
    if len(parts) == 1:
        # Montrek base append
        return "Montrek Base"
    return parts[0].replace("mt_", "").replace("_", " ").title()


def get_app_choices(
    include_contrib=False, only_first_party=True
) -> list[tuple[str, list[str]]]:
    groups = defaultdict(list)

    for cfg in sorted(django_apps.get_app_configs(), key=lambda c: c.name):
        if not include_contrib and cfg.name.startswith("django.contrib."):
            continue
        if only_first_party and "site-packages" in (cfg.path or ""):
            continue

        key = get_group_key(cfg)
        groups[key].append((cfg.label, f"{cfg.verbose_name}"))

    # Sort groups alphabetically by group key
    return [(key, groups[key]) for key in sorted(groups)]


def _split_into_columns(items, n_cols=2):
    """Split a list into n contiguous, near-equal columns."""
    if n_cols < 1:
        n_cols = 1
    length = len(items)
    per = math.ceil(length / n_cols)
    return [items[i * per : (i + 1) * per] for i in range(n_cols)]


class AppSelectForm(MontrekReportForm):
    form_template = "app_select_form.html"
    apps_field = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Pick one or more apps.",
    )

    def __init__(self, *args, **kwargs):
        self._n_columns = int(kwargs.pop("columns", 3))
        super().__init__(*args, **kwargs)
        self.fields["apps_field"].choices = get_app_choices()

    @property
    def apps_grouped(self):
        """
        Yield: [ (group_label, [subwidget, subwidget, ...]), ... ]
        """
        grouped = []
        raw = self.fields["apps_field"].choices
        widgets = {w.data["value"]: w for w in self["apps_field"]}

        for group_label, entries in raw:
            sub = []
            for value, _ in entries:
                if value in widgets:
                    sub.append(widgets[value])
            grouped.append((group_label, sub))
        return grouped

    @property
    def apps_columns(self):
        """
        Returns a list of columns, each a list of subwidgets.
        Example (2 cols): [ [cb0, cb1, ...], [cbX, cbY, ...] ]
        """
        subwidgets = list(self["apps_field"])  # Bound subwidgets reflect checked state
        return _split_into_columns(subwidgets, self._n_columns)
