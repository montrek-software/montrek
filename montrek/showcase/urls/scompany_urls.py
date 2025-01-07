from django.urls import path
from showcase.views.scompany_views import SCompanyDetailView, SCompanyListView
from showcase.views.scompany_views import SCompanyCreateView
from showcase.views.scompany_views import SCompanyUpdateView
from showcase.views.scompany_views import SCompanyDeleteView

urlpatterns = [
    path(
        "scompany/list",
        SCompanyListView.as_view(),
        name="scompany_list",
    ),
    path(
        "scompany/create",
        SCompanyCreateView.as_view(),
        name="scompany_create",
    ),
    path(
        "scompany/<int:pk>/delete",
        SCompanyDeleteView.as_view(),
        name="scompany_delete",
    ),
    path(
        "scompany/<int:pk>/update",
        SCompanyUpdateView.as_view(),
        name="scompany_update",
    ),
    path(
        "scompany/<int:pk>/details",
        SCompanyDetailView.as_view(),
        name="scompany_details",
    ),
]
