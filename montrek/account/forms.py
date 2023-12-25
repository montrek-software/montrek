from baseclasses.forms import MontrekCreateForm


class AccountCreateForm(MontrekCreateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_link_choice_field(
            link_name="link_hub_a_hub_b",
            queryset=self.repository.get_hub_b_objects(),
        )
