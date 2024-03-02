from django.contrib.auth import get_user_model
from django.test import TestCase
from company.tests.factories.company_factories import (
    CompanyStaticSatelliteFactory,
    CompanyTimeSeriesSatelliteFactory,
)
from company.repositories.company_repository import CompanyRepository
from user.tests.factories.montrek_user_factories import MontrekUserFactory


class CompanyRepositoryTest(TestCase):
    def setUp(self):
        self.companies = CompanyStaticSatelliteFactory.create_batch(3)
        self.user = MontrekUserFactory()

    def test_std_queryset(self):
        companies = CompanyRepository().std_queryset()
        self.assertEqual(len(companies), 3)
        for i in range(3):
            self.assertEqual(companies[i].company_name, self.companies[i].company_name)
            self.assertEqual(
                companies[i].bloomberg_ticker,
                self.companies[i].bloomberg_ticker,
            )
            self.assertEqual(
                companies[i].effectual_company_id,
                self.companies[i].effectual_company_id,
            )

    def test_create_and_update_data_and_history_query(self):
        input_data = {"company_name": "TestCompany", "effectual_company_id": "TST"}
        repository = CompanyRepository(session_data={"user_id": self.user.id})
        repository.std_create_object(input_data)
        companies = repository.std_queryset()
        self.assertEqual(len(companies), 4)
        self.assertEqual(companies[3].company_name, "TestCompany")
        self.assertEqual(companies[3].effectual_company_id, "TST")
        input_data = {
            "company_name": "UnitedTestCompany",
            "effectual_company_id": "TST",
        }
        repository.std_create_object(input_data)
        companies = repository.std_queryset()
        self.assertEqual(len(companies), 4)
        self.assertEqual(companies[3].company_name, "UnitedTestCompany")
        self.assertEqual(companies[3].effectual_company_id, "TST")

        history_qs = repository.get_history_queryset(pk=companies[3].id)
        self.assertEqual(len(history_qs), 2)
        self.assertEqual(history_qs[1].company_name, "TestCompany")
        self.assertEqual(history_qs[0].company_name, "UnitedTestCompany")
        self.assertGreater(history_qs[0].change_date, history_qs[1].change_date)

    def test_get_all_time_series(self):
        for company in self.companies:
            CompanyTimeSeriesSatelliteFactory.create_batch(
                5, hub_entity=company.hub_entity
            )
            time_series = CompanyRepository().get_all_time_series(
                self.companies[0].hub_entity.id
            )

            self.assertEqual(len(time_series), 5)
