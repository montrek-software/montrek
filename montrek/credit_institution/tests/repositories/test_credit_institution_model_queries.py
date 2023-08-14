from django.test import TestCase
from credit_institution.repositories.credit_institution_model_queries import (
    new_credit_institution,
)
from credit_institution.repositories.credit_institution_model_queries import (
    new_credit_institution_to_account,
)
from credit_institution.repositories.credit_institution_model_queries import (
    get_credit_institution_satellite_by_account_hub,
)
from credit_institution.repositories.credit_institution_model_queries import (
    get_credit_institution_satellite_by_account_hub_id,
)
from account.tests.factories.account_factories import AccountHubFactory
from credit_institution.models import CreditInstitutionStaticSatellite
from credit_institution.models import CreditInstitutionHub


class TestCreditInstitutionModelQueries(TestCase):
    def test_new_credit_instutition(self):
        credit_institution_hub = new_credit_institution(
            credit_institution_name="Test Credit Institution",
        )
        credit_institution_sat_db = CreditInstitutionStaticSatellite.objects.last()
        self.assertEqual(
            credit_institution_sat_db.credit_institution_name, "Test Credit Institution"
        )
        self.assertEqual(credit_institution_hub, credit_institution_sat_db.hub_entity)

    def test_new_credit_institution_to_account_and_get(self):
        account_hub = AccountHubFactory.create()
        new_credit_institution_to_account(
            credit_institution_name="Test Credit Institution",
            account_hub=account_hub,
        )
        credit_institution_sat_db = CreditInstitutionStaticSatellite.objects.last()
        self.assertEqual(
            credit_institution_sat_db.credit_institution_name, "Test Credit Institution"
        )
        credit_institution_hub = CreditInstitutionHub.objects.last()
        self.assertEqual(credit_institution_hub.link_credit_institution_account.all().first(), account_hub)
        self.assertEqual(
            account_hub.link_account_credit_institution.all().first(), credit_institution_hub
        )
        # When trying to create a new credit institution with the same name, it should not create a new one
        new_credit_institution_to_account(
            credit_institution_name="Test Credit Institution",
            account_hub=account_hub,
        )
        self.assertEqual(CreditInstitutionStaticSatellite.objects.count(), 1)
        self.assertEqual(CreditInstitutionHub.objects.count(), 1)
        # Get the credit institution
        self.assertEqual(
            get_credit_institution_satellite_by_account_hub_id(
                account_id=account_hub.id
            ),
            credit_institution_sat_db,
        )
        self.assertEqual(
            get_credit_institution_satellite_by_account_hub(
                account_hub_object=account_hub
            ),
            credit_institution_sat_db,
        )
