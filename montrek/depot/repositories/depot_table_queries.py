import datetime
from django.db.models import F, Q, Sum, DecimalField
from django.db.models import OuterRef, Subquery, Min
from django.db.models import QuerySet, DurationField, ExpressionWrapper
from account.models import AccountHub
from asset.models import AssetHub
from asset.models import AssetTimeSeriesSatellite


def get_depot_asset_table(account_hub_id: int, reference_date: datetime.date) -> QuerySet:
    # Step 1: Subquery to get the closest date difference
    closest_date_difference = AssetTimeSeriesSatellite.objects.filter(
        hub_entity=OuterRef('pk'),
        value_date__lte=reference_date
    ).annotate(
        date_difference=ExpressionWrapper(
            F('value_date') - reference_date, output_field=DurationField()
        )
    ).order_by('date_difference')


    # Step 2: Your main query
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
        current_price=Subquery(closest_date_difference.values('price')[:1]),
        value_date=Subquery(closest_date_difference.values('value_date')[:1]),
        book_price=ExpressionWrapper(
            F('book_value') / F('total_nominal'),
            output_field=DecimalField()
        ),
        current_value=ExpressionWrapper(
            F('total_nominal') * F('current_price'),
            output_field=DecimalField()
        ),
        performance=ExpressionWrapper(
            (F('current_value') - F('book_value')) / F('book_value'),
            output_field=DecimalField()
        ),
    ).filter(~Q(total_nominal=0))
    return assets_linked_to_account
