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

import os

from baseclasses import views as base_views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", base_views.home, name="home"),
    path("navbar", base_views.navbar, name="navbar"),
    path("links", base_views.links, name="links"),
    path(
        "under_construction", base_views.under_construction, name="under_construction"
    ),
    path("admin/", admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

for app in settings.INSTALLED_APPS:
    app_path = app.replace(".", "/") + "/"
    app_path = str(settings.BASE_DIR) + os.sep + app_path
    if os.path.exists(f"{app_path}/urls.py") or os.path.exists(f"{app_path}/urls"):
        urlpatterns.append(path(app_path, include(f"{app}.urls")))


if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += debug_toolbar_urls()
