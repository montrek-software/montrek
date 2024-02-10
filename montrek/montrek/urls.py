"""
URL configuration for montrek project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from baseclasses import views as base_views

urlpatterns = [
    path("", base_views.home, name="home"),
    path("navbar", base_views.navbar, name="navbar"),
    path(
        "under_construction", base_views.under_construction, name="under_construction"
    ),
    path("admin/", admin.site.urls),
    path("account/", include("account.urls")),
    path("baseclasses/", include("baseclasses.urls")),
    path("file_upload/", include("file_upload.urls")),
    path("transaction/", include("transaction.urls")),
    path("asset/", include("asset.urls")),
    path("credit_institution/", include("credit_institution.urls")),
    path("currency/", include("currency.urls")),
    path("country/", include("country.urls")),
    path("montrek_example/", include("montrek_example.urls")),
    path("user/", include("user.urls")),
]
