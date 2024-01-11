from account.repositories.account_repository import AccountRepository
from asset.repositories.asset_repository import AssetRepository
from baseclasses.forms import MontrekCreateForm
from transaction.repositories.transaction_category_repository import TransactionCategoryRepository



class TransactionCreateForm(MontrekCreateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_link_choice_field(
            display_field="account_name",
            link_name="link_transaction_account",
            queryset=AccountRepository({}).std_queryset(),
        )
        self.add_link_choice_field(
            display_field="asset_name",
            link_name="link_transaction_asset",
            queryset=AssetRepository({}).std_queryset(),
        )
        self.add_link_choice_field(
            display_field="typename",
            link_name="link_transaction_transaction_category",
            queryset=TransactionCategoryRepository({}).std_queryset(),
        )

class TransactionCategoryMapCreateForm(MontrekCreateForm):
    class Meta:
        exclude = ('hash_searchfield',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_link_choice_field(
            display_field="account_name",
            link_name="link_transaction_category_map_account",
            queryset=AccountRepository({}).std_queryset(),
        )
        self.add_link_choice_field(
            display_field="account_name",
            link_name="link_transaction_category_map_counter_transaction_account",
            queryset=AccountRepository({}).std_queryset(),
        )
