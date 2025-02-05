from django.urls import path
from user.views.montrek_user_views import MontrekUserListView
from user.views.montrek_user_views import MontrekUserCreateView
from user.views.montrek_user_views import MontrekUserUpdateView
from user.views.montrek_user_views import MontrekUserDeleteView
from user.views.montrek_user_views import MontrekUserDetailView

urlpatterns = [
    path(
        "montrek_user/list",
        MontrekUserListView.as_view(),
        name="montrek_user_list",
    ),
    path(
        "montrek_user/create",
        MontrekUserCreateView.as_view(),
        name="montrek_user_create",
    ),
    path(
        "montrek_user/<int:pk>/delete",
        MontrekUserDeleteView.as_view(),
        name="montrek_user_delete",
    ),
    path(
        "montrek_user/<int:pk>/update",
        MontrekUserUpdateView.as_view(),
        name="montrek_user_update",
    ),
    path(
        "montrek_user/<int:pk>/details",
        MontrekUserDetailView.as_view(),
        name="montrek_user_details",
    ),
]
