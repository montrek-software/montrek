from django.urls import path
from showcase.views.transaction_views import (
    TransactionListView,
    delete_all_transaction_data,
    load_transaction_example_data,
)
from showcase.views.transaction_views import TransactionCreateView
from showcase.views.transaction_views import TransactionUpdateView
from showcase.views.transaction_views import TransactionDeleteView

urlpatterns = [
    path(
        "transaction/list",
        TransactionListView.as_view(),
        name="transaction_list",
    ),
    path(
        "transaction/create",
        TransactionCreateView.as_view(),
        name="transaction_create",
    ),
    path(
        "transaction/<int:pk>/delete",
        TransactionDeleteView.as_view(),
        name="transaction_delete",
    ),
    path(
        "transaction/<int:pk>/update",
        TransactionUpdateView.as_view(),
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
