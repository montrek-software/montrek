from rest_framework_simplejwt import views as jwt_views

from user.views import PasswordLoginMixin

# montrek's own tokens, for the Django password. With OIDC, API clients take
# their token from the provider instead (authentication.py).


class MontrekTokenObtainPairView(PasswordLoginMixin, jwt_views.TokenObtainPairView):
    pass


class MontrekTokenRefreshView(PasswordLoginMixin, jwt_views.TokenRefreshView):
    pass


class MontrekTokenVerifyView(PasswordLoginMixin, jwt_views.TokenVerifyView):
    pass
