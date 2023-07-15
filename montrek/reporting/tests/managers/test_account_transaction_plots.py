import pandas as pd
from decimal import Decimal
import factory
import numpy as np
from faker import Faker
from django.test import TestCase
import plotly.graph_objects as go
from django.utils import timezone
from django_pandas.io import read_frame
from reporting.managers.account_transaction_plots import draw_monthly_income_expanses_plot
from account.tests.factories.account_factories import AccountHubFactory
from transaction.tests.factories.transaction_factories import TransactionSatelliteFactory
from link_tables.tests.factories.link_tables_factories import AccountTransactionLinkFactory
from transaction.repositories.transaction_account_queries import get_transactions_by_account_hub


class TestAccountTransactionPlots(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.account_hub = AccountHubFactory()
        trans_date_range = pd.date_range(start='2020-01-01', 
                                         end='2022-12-31', 
                                         freq='W')
        trans_date_range_iter = iter(trans_date_range)
        sample_len = len(trans_date_range)
        income_vals = iter(np.random.normal(3000, 500, sample_len))
        expanse_vals = iter(np.random.normal(-2000, 500, sample_len))
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
        transactions_hubs = iter([transaction.hub_entity for transaction in transactions])
        AccountTransactionLinkFactory.create_batch(
            sample_len*2,
            from_hub=factory.Sequence(lambda _: next(iter([cls.account_hub for _ in range(sample_len*2)]))),
            to_hub=factory.Sequence(lambda _: next(iter(transactions_hubs))),
        )



    def test_get_monthly_income_expanses_plot(self):
        transactions = get_transactions_by_account_hub(self.account_hub.id)
        transactions_data = read_frame(transactions)
        test_plot = draw_monthly_income_expanses_plot(transactions_data)
        self.assertTrue(isinstance(test_plot, go.Figure))


