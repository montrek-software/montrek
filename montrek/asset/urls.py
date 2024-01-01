from django.urls import path
from asset import views

urlpatterns = [
    path(
        "overview",
        views.AssetOverview.as_view(),
        name="asset",
    ),
    path(
        "create",
        views.AssetCreateView.as_view(),
        name="asset_create",
    ),
    path(
        "details/<int:pk>",
        views.AssetDetailsView.as_view(),
        name="asset_details",
    ),
    path(
        "update_asset_prices/<int:account_id>",
        views.view_update_asset_prices,
        name="update_asset_prices",
    ),
    path(
        "add_single_price_to_asset/<int:account_id>/<int:asset_id>",
        views.AssetTimeSeriesCreateView.as_view(),
        name="add_single_price_to_asset",
    ),
]
