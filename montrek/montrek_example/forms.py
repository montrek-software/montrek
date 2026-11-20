from django import forms

from baseclasses.forms import MontrekCreateForm, MontrekParameterForm


class ExampleABaseForm(MontrekCreateForm): ...


class ExampleACreateForm(ExampleABaseForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_link_choice_field(
            display_field="field_b1_str",
            link_name="link_hub_a_hub_b",
            queryset=self.repository.get_hub_b_objects(),
            readonly=True,
        )
        self.add_link_choice_field(
            display_field="field_c1_str",
            link_name="link_hub_a_hub_c",
            queryset=self.repository.get_hub_c_objects(),
            is_char_field=True,
        )


class ExampleBCreateForm(MontrekCreateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_link_choice_field(
            display_field="field_d1_str",
            link_name="link_hub_b_hub_d",
            queryset=self.repository.get_hub_d_objects(),
            use_checkboxes_for_many_to_many=False,
            separator=",",
        )


class ExampleCCreateForm(MontrekCreateForm):
    field_order = ["field_c1_str"]

    class Meta:
        exclude: list[str] = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ExampleFactorForm(MontrekParameterForm):
    """Factor the computed TestField column multiplies A2 Float by."""

    session_key = "example_factor"
    factor = forms.IntegerField(
        label="TestField Factor", initial=2, min_value=1, max_value=10
    )
