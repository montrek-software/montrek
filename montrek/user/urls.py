from django.urls import path

from user import views

urlpatterns = [
    path("signup/", views.MontrekSignUpView.as_view(), name="signup"),
    path("login/", views.MontrekLoginView.as_view(), name="login"),
    # todo: get this to work with montrek view
    path("logout/", views.auth_views.LogoutView.as_view(next_page="login"), name="logout"),
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
    path("password_change", views.MontrekPasswordChangeView.as_view(), name="password_change"),
]
