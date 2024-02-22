from baseclasses.forms import MontrekCreateForm


class CompanyCreateForm(MontrekCreateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
