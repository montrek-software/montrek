import math

from django import forms
from django.apps import apps as django_apps
from reporting.forms import MontrekReportForm


def get_app_choices(include_contrib=False, only_first_party=True):
    """
    Build (value, label) tuples for installed apps.

    value: the app label (unique, stable; e.g. "auth", "admin", "myapp")
    label: human-friendly name; e.g. "Authentication and Authorization (django.contrib.auth)"
    """
    choices = []
    for cfg in sorted(django_apps.get_app_configs(), key=lambda c: c.name):
        # Filter options if desired
        if not include_contrib and cfg.name.startswith("django.contrib."):
            continue
        if only_first_party and "site-packages" in (cfg.path or ""):
            continue

        value = cfg.label
        nice = f"{cfg.verbose_name} ({cfg.name})"
        choices.append((value, nice))
    return choices


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
    def apps_columns(self):
        """
        Returns a list of columns, each a list of subwidgets.
        Example (2 cols): [ [cb0, cb1, ...], [cbX, cbY, ...] ]
        """
        subwidgets = list(self["apps_field"])  # Bound subwidgets reflect checked state
        return _split_into_columns(subwidgets, self._n_columns)
