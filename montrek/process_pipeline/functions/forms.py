"""Form fields for letting a user choose what a pipeline should run."""

from django import forms

from process_pipeline.functions.processor_functions import get_function_choices


class FunctionSelectionFormMixin:
    """Adds the fields for picking a processor function and its settings.

    Mix into any form that lets a user choose what a pipeline should run and call
    :meth:`add_function_fields` after ``super().__init__``. The ``settings`` field
    only appears when the functions class ships settings files to choose from.
    """

    select_widget_attrs = {"class": "form-control"}

    def add_function_fields(self, functions_class: type) -> None:
        self.fields["function"] = forms.ChoiceField(
            choices=get_function_choices(functions_class),
            widget=forms.Select(attrs=self.select_widget_attrs),
        )
        settings_choices = self.get_settings_choices(functions_class)
        if settings_choices:
            self.fields["settings"] = forms.ChoiceField(
                choices=settings_choices,
                widget=forms.Select(attrs=self.select_widget_attrs),
            )

    @staticmethod
    def get_settings_choices(functions_class: type) -> list[tuple[str, str]]:
        """Return the packaged settings a user may pick, empty when there are none."""
        if not getattr(functions_class, "has_settings", False):
            return []
        return functions_class.get_settings_choices()
