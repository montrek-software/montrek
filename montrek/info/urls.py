from django.urls import path
from info.views import info_views as views

urlpatterns = [
    path("info", views.InfoVersionsView.as_view(), name="info"),
    path("admin", views.InfoAdminView.as_view(), name="admin"),
]
