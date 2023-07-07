import pandas as pd
from typing import List
from account.models import AccountHub
from credit_institution.models import CreditInstitutionStaticSatellite
from link_tables.models import AccountCreditInstitutionLink
from transaction.models import TransactionSatellite
from baseclasses.repositories.db_helper import select_satellite
from baseclasses.repositories.db_helper import get_link_to_hub
from transaction.repositories.transaction_account_queries import new_transactions_to_account_from_df

def upload_dkb_transactions(account_hub: AccountHub,
                            file_path: str) -> List[TransactionSatellite]:
    credit_institution_hub = get_link_to_hub(account_hub,
                                             AccountCreditInstitutionLink) 
    credit_institution = select_satellite(credit_institution_hub,
                                          CreditInstitutionStaticSatellite)
    if credit_institution.account_upload_method != 'dkb':
        raise AttributeError('Account Upload Method is not of type dkb')
    transactions_df = read_dkb_transactions_from_csv(file_path)
    return new_transactions_to_account_from_df(account_hub, transactions_df)

def read_dkb_transactions_from_csv(file_path: str) -> pd.DataFrame:
    transactions_df = pd.read_csv(file_path,
                                  sep=';',
                                  decimal=',',
                                  thousands='.',
                                  encoding='iso-8859-1',
                                  header=4,
                                  engine='python',
                                  parse_dates=['Buchungstag', 'Wertstellung'],
                                  dayfirst=True,
                                 )
    transaction_df = transactions_df.loc[:,['Buchungstext',
                                          'Verwendungszweck',
                                          'Betrag (EUR)',
                                          'Buchungstag',
                                         ]]
    transaction_df = transaction_df.rename(columns={'Buchungstag': 'transaction_date',
                                                    'Verwendungszweck': 'transaction_description',
                                                    'Betrag (EUR)': 'transaction_amount',
                                                    'Buchungstext': 'transaction_type',
                                                   })
    transaction_df['transaction_price'] = 1.0
    transaction_df['transaction_category'] = transaction_df.apply(
        lambda x: 'INCOME' if x['transaction_amount'] > 0 else 'EXPENSE',
        axis=1)
    return transaction_df

