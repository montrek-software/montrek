from django.urls import path
from showcase.views.transaction_views import (
    STransactionListView,
    delete_all_transaction_data,
    load_transaction_example_data,
)
from showcase.views.transaction_views import STransactionCreateView
from showcase.views.transaction_views import STransactionUpdateView
from showcase.views.transaction_views import STransactionDeleteView

urlpatterns = [
    path(
        "transaction/list",
        STransactionListView.as_view(),
        name="transaction_list",
    ),
    path(
        "transaction/create",
        STransactionCreateView.as_view(),
        name="transaction_create",
    ),
    path(
        "transaction/<int:pk>/delete",
        STransactionDeleteView.as_view(),
        name="transaction_delete",
    ),
    path(
        "transaction/<int:pk>/update",
        STransactionUpdateView.as_view(),
        name="transaction_update",
    ),
    path(
        "transaction/load_transaction_example_data",
        load_transaction_example_data,
        name="load_transaction_example_data",
    ),
    path(
        "transaction/delete_all_transaction_data",
        delete_all_transaction_data,
        name="delete_all_transaction_data",
    ),
]
