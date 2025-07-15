from django.urls import path
from django.conf import settings

from user import views

urlpatterns = [
    path("signup/", views.MontrekSignUpView.as_view(), name="signup"),
    path("login/", views.MontrekLoginView.as_view(), name="login"),
    path("logout/", views.MontrekLogoutView.as_view(next_page="login"), name="logout"),
    path(
        "password_reset/",
        views.MontrekPasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "password_reset_confirm/<uidb64>/<token>/",
        views.MontrekPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password_reset_complete",
        views.MontrekPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path(
        "password_change",
        views.MontrekPasswordChangeView.as_view(),
        name="password_change",
    ),
]
if settings.ENABLE_KEYCLOAK:
    from mozilla_django_oidc import views as oidc_views

    urlpatterns += [
        path(
            "oidc/authenticate/",
            oidc_views.OIDCAuthenticationRequestView.as_view(),
            name="oidc_authentication_init",
        ),
        path(
            "oidc/callback/",
            oidc_views.OIDCAuthenticationCallbackView.as_view(),
            name="oidc_authentication_callback",
        ),
        path("oidc/logout/", oidc_views.OIDCLogoutView.as_view(), name="oidc_logout"),
    ]
