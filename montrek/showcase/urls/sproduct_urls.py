from django.urls import path
from showcase.views.sproduct_views import (
    SProductListView,
    SProductSPositionListView,
    SProductSTransactionListView,
    init_showcase_data,
)
from showcase.views.sproduct_views import SProductCreateView
from showcase.views.sproduct_views import SProductUpdateView
from showcase.views.sproduct_views import SProductDeleteView
from showcase.views.sproduct_views import SProductDetailView

urlpatterns = [
    path(
        "sproduct/list",
        SProductListView.as_view(),
        name="showcase",
    ),
    path(
        "sproduct/create",
        SProductCreateView.as_view(),
        name="sproduct_create",
    ),
    path(
        "sproduct/<int:pk>/delete",
        SProductDeleteView.as_view(),
        name="sproduct_delete",
    ),
    path(
        "sproduct/<int:pk>/update",
        SProductUpdateView.as_view(),
        name="sproduct_update",
    ),
    path(
        "sproduct/init_showcase_data",
        init_showcase_data,
        name="init_showcase_data",
    ),
    path(
        "sproduct/<int:pk>/details",
        SProductDetailView.as_view(),
        name="sproduct_details",
    ),
    path(
        "sproduct/<int:pk>/transactions",
        SProductSTransactionListView.as_view(),
        name="sproduct_stransaction_list",
    ),
    path(
        "sproduct/<int:pk>/positions",
        SProductSPositionListView.as_view(),
        name="sproduct_sposition_list",
    ),
]
