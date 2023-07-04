import pandas as pd
from account.models import AccountHub
from credit_institution.models import CreditInstitutionStaticSatellite
from link_tables.models import AccountCreditInstitutionLink
from baseclasses.model_utils import select_satellite
from baseclasses.model_utils import get_link_to_hub

def upload_dkb_transactions(account_hub: AccountHub,
                            file_path: str) -> None:
    credit_institution_hub = get_link_to_hub(account_hub,
                                             AccountCreditInstitutionLink) 
    credit_institution = select_satellite(credit_institution_hub,
                                          CreditInstitutionStaticSatellite)
    if credit_institution.account_upload_method != 'dkb':
        raise AttributeError('Account Upload Method is not of type dkb')
    transactions_df = read_dkb_transactions(file_path)

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
    return transactions_df.loc[:, ['Wertstellung',
                                   'Buchungstext',
                                   'Auftraggeber / Begünstigter',
                                   'Verwendungszweck',
                                   'Betrag (EUR)',
                                  ]]
