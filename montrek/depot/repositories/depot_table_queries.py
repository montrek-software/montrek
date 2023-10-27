import datetime
from django.db.models import F, Q, Sum, DecimalField
from django.db.models import QuerySet
from account.models import AccountHub
from asset.models import AssetHub


def get_depot_asset_table(account_hub_id: int, reference_date: datetime.date) -> QuerySet:
    assets_linked_to_account = AssetHub.objects.filter(
        Q(link_asset_transaction__link_transaction_account__id=account_hub_id) &
        Q(link_asset_transaction__transaction_satellite__transaction_date__lte=reference_date)
    ).annotate(
        asset_name=F('asset_static_satellite__asset_name'),
        asset_isin=F('asset_liquid_satellite__asset_isin'),
        asset_wkn=F('asset_liquid_satellite__asset_wkn'),
        total_nominal=Sum('link_asset_transaction__transaction_satellite__transaction_amount'),
        book_value=Sum(
            F('link_asset_transaction__transaction_satellite__transaction_amount') *
            F('link_asset_transaction__transaction_satellite__transaction_price'),
            output_field=DecimalField()
        ),
    ).filter(~Q(total_nominal=0))
    return assets_linked_to_account
