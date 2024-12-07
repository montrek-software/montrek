from django.urls import path
from showcase.views.sproduct_views import (
    SProductListView,
    delete_all_sproduct_data,
    load_sproduct_example_data,
)
from showcase.views.sproduct_views import SProductCreateView
from showcase.views.sproduct_views import SProductUpdateView
from showcase.views.sproduct_views import SProductDeleteView

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
        "sproduct/load_sproduct_example_data",
        load_sproduct_example_data,
        name="load_sproduct_example_data",
    ),
    path(
        "sproduct/delete_all_sproduct_data",
        delete_all_sproduct_data,
        name="delete_all_sproduct_data",
    ),
]
