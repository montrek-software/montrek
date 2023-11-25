import re
from django.db import models
from django.db.models import Sum, F
from baseclasses import models as baseclass_models
from baseclasses.repositories.db_helper import select_satellite
from transaction.repositories.transaction_account_queries import (
    get_transactions_by_account_hub,
)
from account.managers.validators import montrek_iban_validator
from depot.managers.depot_stats import DepotStats

# Create your models here.


class AccountHub(baseclass_models.MontrekHubABC):
    link_account_credit_institution = models.ManyToManyField(
        "credit_institution.CreditInstitutionHub",
        related_name="link_credit_institution_account",
    )
    link_account_transaction = models.ManyToManyField(
        "transaction.TransactionHub", related_name="link_transaction_account"
    )
    link_account_file_upload_registry = models.ManyToManyField(
        "file_upload.FileUploadRegistryHub",
        related_name="link_file_upload_registry_account",
    )
    link_account_transaction_category_map = models.ManyToManyField(
        "transaction.TransactionCategoryMapHub",
        related_name="link_transaction_category_map_account",
    )


class AccountStaticSatellite(baseclass_models.MontrekSatelliteABC):
    class AccountType(models.TextChoices):
        OTHER = "Other"
        BANK_ACCOUNT = "BankAccount"
        CASH = "Cash"
        DEPOT = "Depot"
        REAL_ESTATE = "RealEstate"

    hub_entity = models.ForeignKey(AccountHub, on_delete=models.CASCADE)
    identifier_fields = ["account_type", "account_name"]
    account_type = models.CharField(
        max_length=15, choices=AccountType.choices, default=AccountType.OTHER
    )
    account_name = models.CharField(max_length=50)

    @property
    def view_name(self):
        if self.account_type == self.AccountType.OTHER:
            return "account_view"
        # https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
        view_rep = re.sub(r"(?<!^)(?=[A-Z])", "_", self.account_type).lower()
        return f"{view_rep}_view"


class BankAccountPropertySatellite(baseclass_models.MontrekSatelliteABC):
    hub_entity = models.ForeignKey(AccountHub, on_delete=models.CASCADE)
    identifier_fields = ["hub_entity_id"]

    @property
    def account_value(self):
        account_statics = select_satellite(
            self.hub_entity, AccountStaticSatellite 
        )
        
        if account_statics.account_type == AccountStaticSatellite.AccountType.BANK_ACCOUNT:
            return self._get_bank_account_value()
        elif account_statics.account_type == AccountStaticSatellite.AccountType.DEPOT:
            return self._get_depot_account_value()
    
    def _get_bank_account_value(self):
        transactions = get_transactions_by_account_hub(self.hub_entity)
        return (
            transactions.aggregate(
                total_value=Sum(F("transaction_amount") * F("transaction_price"))
            )["total_value"]
            or 0
        )

    def _get_depot_account_value(self):
        return DepotStats(self.hub_entity, timezone.now()).current_value



class BankAccountStaticSatellite(baseclass_models.MontrekSatelliteABC):
    hub_entity = models.ForeignKey(AccountHub, on_delete=models.CASCADE)
    identifier_fields = ["bank_account_iban"]
    bank_account_iban = models.CharField(
        max_length=34,
        validators=[montrek_iban_validator()],
        default="XX00000000000000000000",
    )
