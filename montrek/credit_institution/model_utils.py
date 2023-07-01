from django.apps import apps

from baseclasses import models as baseclass_models
from baseclasses.model_utils import new_link_entry
from baseclasses.model_utils import new_satellite_entry
from baseclasses.model_utils import select_satellite

def credit_institution_hub():
    return apps.get_model('credit_institution','CreditInstitutionHub')

def credit_institution_static_satellite():
    return apps.get_model('credit_institution','CreditInstitutionStaticSatellite')

def account_credit_institution_link():
    return apps.get_model('link_tables','AccountCreditInstitutionLink')

def account_hub():
    return apps.get_model('account','AccountHub')

def new_credit_institution(credit_institution_name:str) -> baseclass_models.MontrekHubABC:
    credit_institution_hub_object = credit_institution_hub().objects.create()
    new_satellite_entry(
        hub_entity=credit_institution_hub_object,
        satellite_class=credit_institution_static_satellite(),
        credit_institution_name=credit_institution_name)
    return credit_institution_hub_object

def new_credit_institution_to_account(credit_institution_name:str,
                                      account_hub:baseclass_models.MontrekHubABC) -> None:
    credit_institution_hub_object = credit_institution_hub().objects.prefetch_related('creditinstitutionstaticsatellite_set').filter(
        creditinstitutionstaticsatellite__credit_institution_name=credit_institution_name).first()
    if not credit_institution_hub_object:
        credit_institution_hub_object = new_credit_institution(credit_institution_name)
    new_link_entry(
        from_hub=account_hub,
        to_hub=credit_institution_hub_object,
        link_table=account_credit_institution_link())

def get_credit_institution_satellite_by_account_hub_id(account_id:int) -> baseclass_models.MontrekSatelliteABC:
    account_hub_object = account_hub().objects.get(id=account_id)
    return get_credit_institution_by_account(account_hub_object)

def get_credit_institution_satellite_by_account_hub(account_hub_object) -> baseclass_models.MontrekSatelliteABC:
    credit_institution_hub = account_credit_institution_link().objects.get(
        from_hub=account_hub_object).to_hub
    return select_satellite(
        credit_institution_hub,
        credit_institution_static_satellite(), 
    )
