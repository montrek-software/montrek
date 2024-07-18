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
from django.conf import settings
from file_upload.tasks.process_file_task import ProcessFileTaskBase
from montrek.celery_app import app as celery_app

urlpatterns = [
    path("", base_views.home, name="home"),
    path("navbar", base_views.navbar, name="navbar"),
    path("links", base_views.links, name="links"),
    path(
        "under_construction", base_views.under_construction, name="under_construction"
    ),
    path("admin/", admin.site.urls),
    path("user/", include("user.urls")),
    path("baseclasses/", include("baseclasses.urls")),
    path("file_upload/", include("file_upload.urls")),
    path("mailing/", include("mailing.urls")),
    path("montrek_example/", include("montrek_example.urls")),
]

for app in settings.MONTREK_EXTENSION_APPS:
    app_path = app.replace(".", "/") + "/"
    urlpatterns.append(path(app_path, include(f"{app}.urls")))


for subclass in ProcessFileTaskBase.__subclasses__():
    celery_app.register_task(subclass)
