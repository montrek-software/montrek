from django.urls import path
from showcase.views.product_views import (
    SProductListView,
    delete_all_product_data,
    load_product_example_data,
)
from showcase.views.product_views import SProductCreateView
from showcase.views.product_views import SProductUpdateView
from showcase.views.product_views import SProductDeleteView

urlpatterns = [
    path(
        "product/list",
        SProductListView.as_view(),
        name="showcase",
    ),
    path(
        "product/create",
        SProductCreateView.as_view(),
        name="product_create",
    ),
    path(
        "product/<int:pk>/delete",
        SProductDeleteView.as_view(),
        name="product_delete",
    ),
    path(
        "product/<int:pk>/update",
        SProductUpdateView.as_view(),
        name="product_update",
    ),
    path(
        "product/load_product_example_data",
        load_product_example_data,
        name="load_product_example_data",
    ),
    path(
        "product/delete_all_product_data",
        delete_all_product_data,
        name="delete_all_product_data",
    ),
]
