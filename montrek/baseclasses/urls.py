from django.urls import path, re_path
from baseclasses import views
from django.views.i18n import JavaScriptCatalog

urlpatterns = [
    path("<int:pk>/details", views.MontrekTemplateView.as_view(), name="dummy_detail"),
    path("client_logo", views.client_logo, name="client_logo"),
]

javascriptcatalog_url = re_path(
    r"^jsi18n/$", JavaScriptCatalog.as_view(), name="jsi18n"
)  # needed for FilteredSelectMultiple widget used in MontrekCreateForm
