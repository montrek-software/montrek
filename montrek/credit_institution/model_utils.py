from django.apps import apps

from baseclasses import models as baseclass_models

def credit_institution_hub():
    return apps.get_model('credit_institution','CreditInstitutionHub')

def credit_institution_static_satellite():
    return apps.get_model('credit_institution','CreditInstitutionStaticSatellite')

def new_credit_institution(credit_institution_name:str) -> baseclass_models.MontrekHubABC:
    credit_institution_hub_object = credit_institution_hub().objects.create()
    credit_institution_static_satellite().objects.create(
        hub_entity=credit_institution_hub_object,
        credit_institution_name=credit_institution_name)
    return credit_institution_hub_object
