from baseclasses.forms import MontrekCreateForm


class ExampleACreateForm(MontrekCreateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_link_choice_field(
            display_field="field_b1_str",
            link_name="link_hub_a_hub_b",
            queryset=self.repository.get_hub_b_objects(),
        )
        self.add_link_choice_field(
            display_field="field_c1_str",
            link_name="link_hub_a_hub_c",
            queryset=self.repository.get_hub_c_objects(),
            is_char_field=True,
            required=True,
        )


class ExampleBCreateForm(MontrekCreateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_link_choice_field(
            display_field="field_d1_str",
            link_name="link_hub_b_hub_d",
            queryset=self.repository.get_hub_d_objects(),
            use_checkboxes_for_many_to_many=False,
        )


class ExampleCCreateForm(MontrekCreateForm):
    class Meta:
        exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
