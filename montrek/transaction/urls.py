from django.urls import path
from transaction import views

urlpatterns = [
    path(
        "add_form/<int:account_id>",
        views.transaction_add_form,
        name="transaction_add_form",
    ),
    path(
        "add/<int:account_id>",
        views.transaction_add,
        name="transaction_add",
    ),
    path(
        "<int:pk>/details/",
        views.TransactionSatelliteDetailView.as_view(),
        name="transaction_details",
    ),
    path(
        "add_transaction_category/<int:account_id>/cp/<str:counterparty>",
        views.TransactionCategoryMapCreateFromTransactionView.as_view(),
        name="transaction_category_add_form_with_counterparty",
    ),
    path(
        "add_transaction_category/<int:account_id>/iban/<str:iban>",
        views.TransactionCategoryMapCreateFromTransactionView.as_view(),
        name="transaction_category_add_form_with_iban",
    ),
    path(
        "add_transaction_category/<int:account_id>",
        views.TransactionCategoryMapCreateView.as_view(),
        name="transaction_category_add_form",
    ),
    path(
        "edit_transcation_category_map/<int:account_id>/<int:pk>",
        views.TransactionCategoryMapUpdateView.as_view(),
        name="transaction_category_map_edit",
    ),
    path(
        "delete_transcation_category_map/<int:account_id>/<int:pk>",
        views.TransactionCategoryMapDeleteView.as_view(),
        name="transaction_category_map_delete",
    ),
]
