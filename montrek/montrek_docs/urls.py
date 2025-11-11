from django.urls import path
from montrek_docs.views import montrek_docs_views as views

urlpatterns = [
    path(
        "montrek_docs/<str:docs_name>",
        views.MontrekDocsView.as_view(),
        name="montrek_docs",
    ),
]
