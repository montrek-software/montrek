from baseclasses.repositories.montrek_repository import MontrekRepository
from .users.vincentmohiuddin.code.montrek.montrek.code_generation.tests.data.output.models.company_hub_models import (
    CompanyHub,
)


class CompanyRepository(MontrekRepository):
    hub_class = CompanyHub

    def set_annotations(self):
        pass
