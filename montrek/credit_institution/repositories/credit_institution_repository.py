from django.utils import timezone
from credit_institution.models import (
    CreditInstitutionHub,
    CreditInstitutionStaticSatellite,
)
from baseclasses.repositories.db_helper import get_satellite_from_hub_query
from baseclasses.repositories.montrek_repository import MontrekRepository


class CreditInstitutionRepository(MontrekRepository):
    hub_class = CreditInstitutionHub

    def std_queryset(self, **kwargs):
        reference_date = timezone.now()
        self.add_satellite_fields_annotations(
            CreditInstitutionStaticSatellite,
            [
                "credit_institution_name",
                "credit_institution_bic",
                "account_upload_method",
            ],
            reference_date,
        )
        return self.build_queryset()

    def get_queryset_with_account(self):
        reference_date = timezone.now()
        self.annotations["account_name"] = get_satellite_from_hub_query(
            "accountstaticsatellite", "account_name", "link_credit_institution_account"
        )
        self.annotations["account_id"] = get_satellite_from_hub_query(
            "accountstaticsatellite", "hub_entity.id", "link_credit_institution_account"
        )
        return self.std_queryset()
