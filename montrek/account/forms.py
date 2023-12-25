from baseclasses.forms import MontrekCreateForm
from credit_institution.repositories.credit_institution_repository import ( CreditInstitutionRepository)


class AccountCreateForm(MontrekCreateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_link_choice_field(
            display_field="credit_institution_name",
            link_name="link_account_credit_institution",
            queryset=CreditInstitutionRepository({}).std_queryset(),
        )
