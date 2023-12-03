from django.urls import path
from account import views

urlpatterns = [
    path("new", views.account_new, name="account_new"),
    path("new_form", views.account_new_form, name="account_new_form"),
    path("list", views.AccountOverview.as_view(), name="account"),
    path("<int:pk>/details", views.AccountDetailView.as_view(), name="account_details"),
    path("<int:account_id>/delete", views.account_delete, name="account_delete"),
    path(
        "<int:account_id>/delete_form",
        views.account_delete_form,
        name="account_delete_form",
    ),
    path(
        "bank_account/new_form/<str:account_name>/<str:account_type>",
        views.bank_account_new_form,
        name="bank_account_new_form",
    ),
    path(
        "bank_account/new/<str:account_name>/<str:account_type>",
        views.bank_account_new,
        name="bank_account_new",
    ),
    path(
        "<int:pk>/bank_account_view/transactions",
        views.AccountTransactionsView.as_view(),
        name="bank_account_view_transactions",
    ),
    path(
        "<int:account_id>/bank_account_view/graphs",
        views.bank_account_view_graphs,
        name="bank_account_view_graphs",
    ),
    path(
        "<int:account_id>/bank_account_view/uploads",
        views.bank_account_view_uploads,
        name="bank_account_view_uploads",
    ),
    path(
        "<int:account_id>/bank_account_view/transaction_category_map",
        views.bank_account_view_transaction_category_map,
        name="bank_account_view_transaction_category_map",
    ),
    path(
        "<int:account_id>/bank_account_view/depot",
        views.bank_account_view_depot,
        name="bank_account_view_depot",
    ),
]
