from django.urls import path
from docs_framework.tests.views import mock_views as views

urlpatterns = [
    path("test_docs/<str:docs_name>", views.MockDocsView.as_view(), name="test_docs"),
]
