from django.urls import path
from showcase.views.product_views import ProductListView, load_product_example_data
from showcase.views.product_views import ProductCreateView
from showcase.views.product_views import ProductUpdateView
from showcase.views.product_views import ProductDeleteView

urlpatterns = [
    path(
        "product/list",
        ProductListView.as_view(),
        name="showcase",
    ),
    path(
        "product/create",
        ProductCreateView.as_view(),
        name="product_create",
    ),
    path(
        "product/<int:pk>/delete",
        ProductDeleteView.as_view(),
        name="product_delete",
    ),
    path(
        "product/<int:pk>/update",
        ProductUpdateView.as_view(),
        name="product_update",
    ),
    path(
        "product/load_product_example_data",
        load_product_example_data,
        name="load_product_example_data",
    ),
]
