import hashlib
from django.db import models
from baseclasses import models as baseclass_models
from account.managers.validators import montrek_iban_validator
from transaction.repositories.transaction_category_queries import (
    get_transaction_category_by_transaction,
)


# Create your models here.
class TransactionHub(baseclass_models.MontrekHubABC):
    link_transaction_transaction_category = models.ManyToManyField(
        "TransactionCategoryHub",
        related_name="link_transaction_category_transaction",
        through="LinkTransactionTransactionCategory",
    )
    link_transaction_transaction_type = models.ManyToManyField(
        "TransactionTypeHub",
        related_name="link_transaction_transaction_type",
        through="LinkTransactionTransactionType",
    )
    link_transaction_asset = models.ManyToManyField(
        "asset.AssetHub",
        related_name="link_asset_transaction",
        through="LinkTransactionAsset",
    )

class LinkTransactionTransactionCategory(baseclass_models.MontrekLinkABC):
    in_hub=models.ForeignKey("transaction.TransactionHub", on_delete=models.CASCADE)
    out_hub=models.ForeignKey("transaction.TransactionCategoryHub", on_delete=models.CASCADE)

class LinkTransactionTransactionType(baseclass_models.MontrekLinkABC):
    in_hub=models.ForeignKey("transaction.TransactionHub", on_delete=models.CASCADE)
    out_hub=models.ForeignKey("transaction.TransactionTypeHub", on_delete=models.CASCADE)

class LinkTransactionAsset(baseclass_models.MontrekLinkABC):
    in_hub=models.ForeignKey("transaction.TransactionHub", on_delete=models.CASCADE)
    out_hub=models.ForeignKey("asset.AssetHub", on_delete=models.CASCADE)


class TransactionSatellite(baseclass_models.MontrekSatelliteABC):
    hub_entity = models.ForeignKey(
        TransactionHub, on_delete=models.CASCADE, related_name="transaction_satellite"
    )
    identifier_fields = [
        "transaction_date",
        "transaction_party",
        "transaction_party_iban",
    ]
    transaction_date = models.DateTimeField()
    transaction_amount = models.DecimalField(max_digits=20, decimal_places=5)
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
        return get_transaction_category_by_transaction(self)


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
    identifier_fields = ["field", "value"]
    hub_entity = models.ForeignKey(TransactionCategoryMapHub, on_delete=models.CASCADE)
    TRANSACTION_PARTY = "transaction_party"
    TRANSACTION_PARTY_IBAN = "transaction_party_iban"

    FIELD_CHOICES = [
        (TRANSACTION_PARTY, "Transaction Party"),
        (TRANSACTION_PARTY_IBAN, "Transaction Party IBAN"),
    ]

    field = models.CharField(
        max_length=25, choices=FIELD_CHOICES, default=TRANSACTION_PARTY
    )
    value = models.CharField(max_length=250, default="")
    category = models.CharField(max_length=250, default="")
    hash_searchfield = models.CharField(max_length=64, default="")
    is_regex = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.hash_searchfield = hashlib.sha256(
            (self.field + str(self.value).replace(" ", "").upper()).encode()
        ).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"TransactionCategoryMapSatellite: {self.field} - {self.value} - {self.category}"
