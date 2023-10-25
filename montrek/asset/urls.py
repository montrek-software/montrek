from django.urls import path
from asset import views

urlpatterns = [
    path(
        "create/<int:account_id>",
        views.AssetCreateView.as_view(),
        name="asset_create_form",
    ),
]
