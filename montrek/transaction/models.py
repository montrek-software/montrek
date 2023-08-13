from django.db import models
import hashlib
from baseclasses import models as baseclass_models
from account import models as account_models
from account.managers.validators import montrek_iban_validator
from transaction.repositories.transaction_model_queries import (
    set_transaction_category_by_map,
)

# Create your models here.
class TransactionHub(baseclass_models.MontrekHubABC):
    link_transaction_transaction_category = models.ManyToManyField(
        "TransactionCategoryHub", 
        related_name = "link_transaction_category_transaction",
    )
    link_transaction_transaction_type = models.ManyToManyField(
        "TransactionTypeHub", 
        related_name = "link_transaction_type_transaction",
    )


class TransactionSatellite(baseclass_models.MontrekSatelliteABC):
    hub_entity = models.ForeignKey(TransactionHub, on_delete=models.CASCADE)
    identifier_fields = [
        "transaction_date",
        "transaction_party",
        "transaction_party_iban",
    ]
    transaction_date = models.DateTimeField()
    transaction_amount = models.IntegerField()
    transaction_price = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_description = models.TextField()
    transaction_party = models.CharField(max_length=250, default="NONE")
    transaction_party_iban = models.CharField(
        max_length=34,
        validators=[montrek_iban_validator()],
        default="XX00000000000000000000",
    )

    @property
    def transaction_value(self):
        return self.transaction_amount * self.transaction_price

    @property
    def transaction_category(self):
        transactioncategory_hub = (
            self.hub_entity.link_transaction_transaction_category.all()
        )
        if len(transactioncategory_hub) == 0:
            transactioncategory_hub = set_transaction_category_by_map(self)
        else:
            transactioncategory_hub = transactioncategory_hub[0]
        return transactioncategory_hub.transactioncategorysatellite_set.all()[0]


class TransactionTypeHub(baseclass_models.MontrekHubABC):
    pass


class TransactionTypeSatellite(
    baseclass_models.MontrekSatelliteABC, baseclass_models.TypeMixin
):
    hub_entity = models.ForeignKey(TransactionTypeHub, on_delete=models.CASCADE)



class TransactionCategoryHub(baseclass_models.MontrekHubABC):
    pass


class TransactionCategorySatellite(
    baseclass_models.MontrekSatelliteABC, baseclass_models.TypeMixin
):
    hub_entity = models.ForeignKey(TransactionCategoryHub, on_delete=models.CASCADE)


class TransactionCategoryMapHub(baseclass_models.MontrekHubABC):
    pass


class TransactionCategoryMapSatellite(baseclass_models.MontrekSatelliteABC):
    identifier_fields = ["field", "value", "category"]
    hub_entity = models.ForeignKey(TransactionCategoryMapHub, on_delete=models.CASCADE)
    field = models.CharField(max_length=250, default="NONE")
    value = models.CharField(max_length=250, default="NONE")
    category = models.CharField(max_length=250, default="NONE")
    hash_searchfield = models.CharField(max_length=64, default="")

    def save(self, *args, **kwargs):
        self.hash_searchfield = hashlib.sha256(
            (self.field + str(self.value).replace(' ','').upper()).encode()
        ).hexdigest()
        super().save(*args, **kwargs)
