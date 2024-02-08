from django import forms

from credit_institution.models import CreditInstitutionStaticSatellite
from country.repositories.country_repository import CountryRepository
from baseclasses.forms import MontrekCreateForm


class CreditInstitutionCreateForm(MontrekCreateForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_link_choice_field(
            display_field="country_name",
            link_name="link_credit_institution_country",
            queryset=CountryRepository().std_queryset(),
        )


