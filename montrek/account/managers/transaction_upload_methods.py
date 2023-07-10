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
                                            'Auftraggeber / Begünstigter',
                                            'Kontonummer',
                                         ]]
    transaction_df = transaction_df.rename(columns={'Buchungstag': 'transaction_date',
                                                    'Verwendungszweck': 'transaction_description',
                                                    'Betrag (EUR)': 'transaction_price',
                                                    'Buchungstext': 'transaction_type',
                                                    'Auftraggeber / Begünstigter': 'transaction_party',
                                                    'Kontonummer': 'transaction_party_iban',
                                                   })
    aggregations = {
        'transaction_description': lambda x: ' '.join(x),
        'transaction_price': lambda x: x.sum(),
    }
    transaction_df = transaction_df.groupby(['transaction_date',
                                             'transaction_type',
                                             'transaction_party',
                                             'transaction_party_iban']).agg(aggregations).reset_index()
    transaction_df['transaction_amount'] = 1
    transaction_df['transaction_category'] = transaction_df.apply(
        lambda x: 'INCOME' if x['transaction_price'] > 0 else 'EXPENSE',
        axis=1)
    return transaction_df

