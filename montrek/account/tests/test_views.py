import os
from django.conf import settings
from django.test import TestCase
from account import views
from account.models import AccountHub
from account.models import AccountStaticSatellite
from account.tests.factories.account_factories import AccountStaticSatelliteFactory
from account.tests.factories.account_factories import BankAccountStaticSatelliteFactory
from transaction.tests.factories.transaction_factories import (
    TransactionSatelliteFactory,
    TransactionCategoryMapSatelliteFactory,
)
from file_upload.tests.factories.file_upload_factories import (
    FileUploadRegistryStaticSatelliteFactory,
)
from asset.tests.factories.asset_factories import AssetStaticSatelliteFactory
from currency.tests.factories.currency_factories import CurrencyStaticSatelliteFactory
from credit_institution.tests.factories.credit_institution_factories import CreditInstitutionStaticSatelliteFactory

from baseclasses.utils import montrek_time


class TestAccountOverview(TestCase):
    def setUp(self):
        AccountStaticSatelliteFactory.create_batch(3)

    def test_account_overview_returns_correct_html(self):
        response = self.client.get("/account/overview")
        self.assertTemplateUsed(response, "montrek_table.html")

    def test_account_overview_context_data(self):
        response = self.client.get("/account/overview")
        context = response.context
        self.assertFalse(context["is_paginated"])
        object_list = context["object_list"]
        self.assertEqual(len(object_list), 3)
        self.assertIsInstance(context["view"], views.AccountOverview)
        self.assertEqual(context["page_title"], "Accounts")


class TestAccountDetailView(TestCase):
    def setUp(self):
        self.acc_sat1 = AccountStaticSatelliteFactory.create()

    def test_account_detail_view_returns_correct_html(self):
        response = self.client.get(f"/account/{self.acc_sat1.hub_entity.id}/details")
        self.assertTemplateUsed(response, "montrek_details.html")

    def test_account_detail_view_context_data(self):
        response = self.client.get(f"/account/{self.acc_sat1.hub_entity.id}/details")
        context = response.context
        self.assertEqual(context["title"], "Account Details")
        self.assertEqual(context["object"], self.acc_sat1.hub_entity)
        self.assertIsInstance(context["view"], views.AccountDetailView)


class TestAccountTransactionsView(TestCase):
    def setUp(self):
        test_session = self.client.session
        test_session["end_date"] = "2023-12-11"
        test_session["start_date"] = "2023-12-09"
        test_session.save()
        self.acc = AccountStaticSatelliteFactory.create()
        for transaction in TransactionSatelliteFactory.create_batch(
            3, transaction_date=montrek_time(2023, 12, 10)
        ):
            transaction.hub_entity.link_transaction_account.add(self.acc.hub_entity)
            transaction.hub_entity.save()

    def test_account_transactions_view_returns_correct_html(self):
        response = self.client.get(f"/account/{self.acc.hub_entity.id}/transactions")
        self.assertTemplateUsed(response, "montrek_table.html")

    def test_account_transactions_view_context_data(self):
        response = self.client.get(f"/account/{self.acc.hub_entity.id}/transactions")
        context = response.context
        self.assertFalse(context["is_paginated"])
        object_list = context["object_list"]
        self.assertEqual(len(object_list), 3)
        self.assertIsInstance(context["view"], views.AccountTransactionsView)
        self.assertEqual(context["page_title"], self.acc.account_name)


class TestAccountGraphView(TestCase):
    def setUp(self):
        test_session = self.client.session
        test_session["end_date"] = "2023-12-11"
        test_session["start_date"] = "2023-12-09"
        test_session.save()
        self.acc = AccountStaticSatelliteFactory.create()
        for transaction in TransactionSatelliteFactory.create_batch(
            3, transaction_date=montrek_time(2023, 12, 10)
        ):
            transaction.hub_entity.link_transaction_account.add(self.acc.hub_entity)
            transaction.hub_entity.save()

    def test_account_graphs_view_returns_correct_html(self):
        response = self.client.get(f"/account/{self.acc.hub_entity.id}/graphs")
        self.assertTemplateUsed(response, "account_graphs.html")

    def test_account_graphs_view_context_data(self):
        response = self.client.get(f"/account/{self.acc.hub_entity.id}/graphs")
        context = response.context
        self.assertIsInstance(context["view"], views.AccountGraphsView)
        self.assertEqual(context["page_title"], self.acc.account_name)
        # Check that graphs are generated divs
        for plot in [
            "income_expanse_plot",
            "income_category_pie_plot",
            "expense_category_pie_plot",
        ]:
            self.assertInHTML(context[plot], response.content.decode())
            plot.startswith("<div>")
            plot.endswith("</div>")


class TestAccountUploadView(TestCase):
    def setUp(self):
        self.acc = AccountStaticSatelliteFactory.create()
        fl_upld_reg = FileUploadRegistryStaticSatelliteFactory.create()
        fl_upld_reg.hub_entity.link_file_upload_registry_account.add(
            self.acc.hub_entity
        )

    def test_account_upload_view_returns_correct_html(self):
        response = self.client.get(f"/account/{self.acc.hub_entity.id}/uploads")
        self.assertTemplateUsed(response, "montrek_table.html")

    def test_account_upload_view_context_data(self):
        response = self.client.get(f"/account/{self.acc.hub_entity.id}/uploads")
        context = response.context
        self.assertIsInstance(context["view"], views.AccountUploadView)
        self.assertEqual(context["page_title"], self.acc.account_name)
        self.assertEqual(len(context["object_list"]), 1)
        self.assertEqual(
            context["object_list"][0],
            self.acc.hub_entity.link_account_file_upload_registry.first(),
        )


class TestAccountTransactionCategoryMapView(TestCase):
    def setUp(self):
        self.acc = AccountStaticSatelliteFactory.create()
        tr_cat_map = TransactionCategoryMapSatelliteFactory.create(
            hub_entity__accounts=(self.acc.hub_entity,)
        )

    def test_account_transaction_category_map_view_returns_correct_html(self):
        response = self.client.get(
            f"/account/{self.acc.hub_entity.id}/transaction_category_map"
        )
        self.assertTemplateUsed(response, "montrek_table.html")

    def test_account_transaction_category_map_view_context_data(self):
        response = self.client.get(
            f"/account/{self.acc.hub_entity.id}/transaction_category_map"
        )
        context = response.context
        self.assertIsInstance(context["view"], views.AccountTransactionCategoryMapView)
        self.assertEqual(context["page_title"], self.acc.account_name)
        self.assertEqual(len(context["object_list"]), 1)
        self.assertEqual(
            context["object_list"][0],
            self.acc.hub_entity.link_account_transaction_category_map.first(),
        )


class TestAccountDepotView(TestCase):
    def setUp(self):
        test_session = self.client.session
        test_session["end_date"] = "2023-12-11"
        test_session["start_date"] = "2023-12-09"
        test_session.save()
        self.acc = AccountStaticSatelliteFactory.create()
        ccy = CurrencyStaticSatelliteFactory.create()
        asset = AssetStaticSatelliteFactory.create(currency=ccy.hub_entity)
        transaction_date = montrek_time(2023, 12, 10)
        for transaction in TransactionSatelliteFactory.create_batch(
            3, transaction_date=transaction_date, hub_entity__account=self.acc.hub_entity
        ):
            transaction.hub_entity.link_transaction_account.add(self.acc.hub_entity)
            transaction.hub_entity.link_transaction_asset.add(asset.hub_entity)
            transaction.hub_entity.save()

    def test_account_depot_view_returns_correct_html(self):
        response = self.client.get(f"/account/{self.acc.hub_entity.id}/depot")
        self.assertTemplateUsed(response, "montrek_table.html")

    def test_account_depot_view_context_data(self):
        response = self.client.get(f"/account/{self.acc.hub_entity.id}/depot")
        context = response.context
        self.assertFalse(context["is_paginated"])
        object_list = context["object_list"]
        self.assertEqual(len(object_list), 1)
        self.assertIsInstance(context["view"], views.AccountDepotView)
        self.assertEqual(context["page_title"], self.acc.account_name)

class TestAccountCreateView(TestCase):
    def test_account_create_view_returns_correct_html(self):
        response = self.client.get("/account/create")
        self.assertTemplateUsed(response, "montrek_create.html")

class TestDKBAccountUploadFileView(TestCase):
    def setUp(self):
        self.acc = AccountStaticSatelliteFactory.create()
        ci_fac = CreditInstitutionStaticSatelliteFactory.create(
            account_upload_method="dkb",
        )
        self.acc.hub_entity.link_account_credit_institution.add(ci_fac.hub_entity)
        self.bcc = BankAccountStaticSatelliteFactory.create(
            hub_entity=self.acc.hub_entity,
        )


    def test_account_upload_file_view_returns_correct_html(self):
        response = self.client.get(f"/account/{self.acc.hub_entity.id}/upload_file")
        self.assertTemplateUsed(response, "upload_form.html")
        self.assertEqual(response.status_code, 200)

    def test_account_upload_file_view_enter_file(self):
        url = f"/account/{self.acc.hub_entity.id}/upload_file"
        test_csv_path = os.path.join(settings.BASE_DIR, "account/tests/managers/data", "dkb_test.csv")
        with open(test_csv_path, "rb") as test_csv:
            response = self.client.post(
                url,
                {"file": test_csv},
                follow=True,
            )
            self.assertTemplateUsed(response, "montrek_table.html")
            self.assertEqual(response.status_code, 200)
