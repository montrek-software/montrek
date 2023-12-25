from django.urls import path
from account import views

urlpatterns = [
    path("create", views.AccountCreateView.as_view(), name="account_create"),
    path("overview", views.AccountOverview.as_view(), name="account"),
    path("<int:pk>/details", views.AccountDetailView.as_view(), name="account_details"),
    path("<int:pk>/delete", views.AccountDeleteView.as_view(), name="account_delete"),
    path("<int:pk>/update", views.AccountUpdateView.as_view(), name="account_update"),
    path(
        "<int:pk>/transactions",
        views.AccountTransactionsView.as_view(),
        name="account_view_transactions",
    ),
    path(
        "<int:pk>/graphs",
        views.AccountGraphsView.as_view(),
        name="account_view_graphs",
    ),
    path(
        "<int:pk>/uploads",
        views.AccountUploadView.as_view(),
        name="account_view_uploads",
    ),
    path(
        "<int:pk>/transaction_category_map",
        views.AccountTransactionCategoryMapView.as_view(),
        name="account_view_transaction_category_map",
    ),
    path(
        "<int:pk>/depot",
        views.AccountDepotView.as_view(),
        name="account_view_depot",
    ),
]
