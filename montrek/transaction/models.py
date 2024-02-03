from django.db import models
from baseclasses import models as baseclass_models
from account.managers.validators import montrek_iban_validator


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


class LinkTransactionTransactionCategory(baseclass_models.MontrekOneToManyLinkABC):
    hub_in = models.ForeignKey("transaction.TransactionHub", on_delete=models.CASCADE)
    hub_out = models.ForeignKey(
        "transaction.TransactionCategoryHub", on_delete=models.CASCADE
    )


class LinkTransactionTransactionType(baseclass_models.MontrekOneToManyLinkABC):
    hub_in = models.ForeignKey("transaction.TransactionHub", on_delete=models.CASCADE)
    hub_out = models.ForeignKey(
        "transaction.TransactionTypeHub", on_delete=models.CASCADE
    )


class LinkTransactionAsset(baseclass_models.MontrekOneToManyLinkABC):
    hub_in = models.ForeignKey("transaction.TransactionHub", on_delete=models.CASCADE)
    hub_out = models.ForeignKey("asset.AssetHub", on_delete=models.CASCADE)


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


class TransactionTypeHub(baseclass_models.MontrekHubABC):
    pass


class TransactionTypeSatellite(baseclass_models.MontrekTypeSatelliteABC):
    hub_entity = models.ForeignKey(TransactionTypeHub, on_delete=models.CASCADE)


class TransactionCategoryHub(baseclass_models.MontrekHubABC):
    pass


class TransactionCategorySatellite(baseclass_models.MontrekTypeSatelliteABC):
    hub_entity = models.ForeignKey(TransactionCategoryHub, on_delete=models.CASCADE)


class TransactionCategoryMapHub(baseclass_models.MontrekHubABC):
    link_transaction_category_map_counter_transaction_account = models.ManyToManyField(
        "account.AccountHub",
        related_name="link_counter_transaction_account_transaction_category_map",
        through="LinkTransactionCategoryMapCounterTransactionAccount",
    )


class LinkTransactionCategoryMapCounterTransactionAccount(
    baseclass_models.MontrekOneToManyLinkABC
):
    hub_in = models.ForeignKey(
        "transaction.TransactionCategoryMapHub", on_delete=models.CASCADE
    )
    hub_out = models.ForeignKey("account.AccountHub", on_delete=models.CASCADE)


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
    is_regex = models.BooleanField(default=False)

    def __str__(self):
        return f"TransactionCategoryMapSatellite: {self.field} - {self.value} - {self.category}"
