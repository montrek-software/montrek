from .montrek_user_urls import urlpatterns as montrek_user_urls
from .montrek_user_auth_urls import urlpatterns as montrek_user_auth_urls

urlpatterns = montrek_user_urls + montrek_user_auth_urls
