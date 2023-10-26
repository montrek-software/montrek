from django.db.models import F, Sum, DecimalField
from django.db.models import QuerySet
from account.models import AccountHub
from asset.models import AssetHub


def get_depot_asset_table(account_hub: AccountHub) -> QuerySet:
    assets_linked_to_account = AssetHub.objects.filter(
        link_asset_transaction__link_transaction_account__id=account_hub.id
    ).annotate(
        asset_name=F('asset_static_satellite__asset_name'),
        asset_isin=F('asset_liquid_satellite__asset_isin'),
        asset_wkn=F('asset_liquid_satellite__asset_wkn'),
        total_nominal=Sum('link_asset_transaction__transaction_satellite__transaction_amount'),
    )
    return assets_linked_to_account
