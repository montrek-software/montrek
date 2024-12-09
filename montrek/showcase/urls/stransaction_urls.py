from django.urls import path
from showcase.views.stransaction_views import (
    STransactionListView,
)
from showcase.views.stransaction_views import STransactionCreateView
from showcase.views.stransaction_views import STransactionUpdateView
from showcase.views.stransaction_views import STransactionDeleteView

urlpatterns = [
    path(
        "stransaction/list",
        STransactionListView.as_view(),
        name="stransaction_list",
    ),
    path(
        "stransaction/create",
        STransactionCreateView.as_view(),
        name="stransaction_create",
    ),
    path(
        "stransaction/<int:pk>/delete",
        STransactionDeleteView.as_view(),
        name="stransaction_delete",
    ),
    path(
        "stransaction/<int:pk>/update",
        STransactionUpdateView.as_view(),
        name="stransaction_update",
    ),
]
