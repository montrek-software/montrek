import pandas as pd
from decimal import Decimal
import factory
import numpy as np
from faker import Faker
from django.test import TestCase
from django.utils import timezone
#from reporting.managers.account_transaction_plots import get_monthly_income_expanses_plot
from account.tests.factories.account_factories import AccountHubFactory
from transaction.tests.factories.transaction_factories import TransactionSatelliteFactory


class TestAccountTransactionPlots(TestCase):
    @classmethod
    def setUpTestData(cls):
        account_hub = AccountHubFactory()
        trans_date_range = pd.date_range(start='2020-01-01', 
                                         end='2022-12-31', 
                                         freq='W')
        trans_date_range_iter = iter(trans_date_range)
        sample_len = len(trans_date_range)
        income_vals = iter(np.random.normal(3000, 500, sample_len))
        expanse_vals = np.random.normal(-2000, 500, sample_len)
        transactions = TransactionSatelliteFactory.create_batch(
            sample_len,
            transaction_price=factory.Sequence(lambda _: next(income_vals)),
            transaction_date=factory.Sequence(lambda _: next(trans_date_range_iter)),
        )


    def test_get_monthly_income_expanses_plot(self):
        pass


