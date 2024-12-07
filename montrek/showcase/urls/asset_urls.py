from django.urls import path
from showcase.views.asset_views import SAssetListView
from showcase.views.asset_views import SAssetCreateView
from showcase.views.asset_views import SAssetUpdateView
from showcase.views.asset_views import SAssetDeleteView

urlpatterns = [
    path(
        "asset/list",
        SAssetListView.as_view(),
        name="asset_list",
    ),
    path(
        "asset/create",
        SAssetCreateView.as_view(),
        name="asset_create",
    ),
    path(
        "asset/<int:pk>/delete",
        SAssetDeleteView.as_view(),
        name="asset_delete",
    ),
    path(
        "asset/<int:pk>/update",
        SAssetUpdateView.as_view(),
        name="asset_update",
    ),
]
