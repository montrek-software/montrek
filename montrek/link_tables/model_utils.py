from django.apps import apps

from baseclasses import models as baseclass_models

def account_credit_institution_link():
    return apps.get_model('link_tables','AccountCreditInstitutionLink')

def new_account_credit_instition_link(account_hub:baseclass_models.MontrekHubABC,
                                      credit_institution_hub:baseclass_models.MontrekHubABC) -> None:
    account_credit_institution_link().objects.create(
        from_hub=account_hub,
        to_hub=credit_institution_hub)
