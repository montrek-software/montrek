from decimal import Decimal
import factory
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from django.test import TestCase
from django_pandas.io import read_frame
from django.utils import timezone
from account.managers.account_transaction_plots import (
    draw_monthly_income_expanses_plot,
    draw_income_expenses_category_pie_plot,
)
from account.tests.factories.account_factories import AccountHubFactory
from transaction.tests.factories.transaction_factories import (
    TransactionSatelliteFactory,
)
from transaction.repositories.transaction_repository import (
    TransactionRepository,
)


class TestAccountTransactionPlots(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.account_hub = AccountHubFactory()
        trans_date_range = pd.date_range(start="2020-01-01", end="2022-12-31", freq="W")
        trans_date_range = trans_date_range.tz_localize(timezone.get_current_timezone())
        trans_date_range_iter = iter(trans_date_range)
        sample_len = len(trans_date_range)
        income_list = np.random.normal(30, 5, sample_len)
        expanse_list = np.random.normal(-20, 5, sample_len)
        income_list = [1000 + income_list[i] * (i) for i in range(sample_len)]
        expanse_list = [-500 + expanse_list[i] * (i) for i in range(sample_len)]
        income_vals = iter(income_list)
        expanse_vals = iter(expanse_list)
        transactions = TransactionSatelliteFactory.create_batch(
            sample_len,
            transaction_price=factory.Sequence(lambda _: next(income_vals)),
            transaction_date=factory.Sequence(lambda _: next(trans_date_range_iter)),
            transaction_amount=factory.Sequence(lambda _: Decimal(1)),
        )
        trans_date_range_iter = iter(trans_date_range)
        transactions += TransactionSatelliteFactory.create_batch(
            sample_len,
            transaction_price=factory.Sequence(lambda _: next(expanse_vals)),
            transaction_date=factory.Sequence(lambda _: next(trans_date_range_iter)),
            transaction_amount=factory.Sequence(lambda _: Decimal(1)),
        )
        for transaction in transactions:
            cls.account_hub.link_account_transaction.add(transaction.hub_entity)

    def test_get_monthly_income_expanses_plot(self):
        transactions = (
            TransactionRepository({})
            .get_queryset_with_account()
            .filter(account_id=self.account_hub.id)
        )
        transactions_data = read_frame(transactions)
        test_plot = draw_monthly_income_expanses_plot(transactions_data)
        self.assertTrue(isinstance(test_plot.figure, go.Figure))

    def test_get_income_by_category_pie_plot(self):
        transactions = (
            TransactionRepository({})
            .get_queryset_with_account()
            .filter(account_id=self.account_hub.id)
        )
        test_plots = draw_income_expenses_category_pie_plot(transactions)
        self.assertTrue(isinstance(test_plots["income"].figure, go.Figure))
        self.assertTrue(isinstance(test_plots["expense"].figure, go.Figure))
