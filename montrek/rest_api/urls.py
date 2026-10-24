from django.urls import path

from rest_api import views

urlpatterns = [
    path(
        "token/", views.MontrekTokenObtainPairView.as_view(), name="token_obtain_pair"
    ),
    path(
        "token/refresh/", views.MontrekTokenRefreshView.as_view(), name="token_refresh"
    ),
    path("token/verify/", views.MontrekTokenVerifyView.as_view(), name="token_verify"),
]
