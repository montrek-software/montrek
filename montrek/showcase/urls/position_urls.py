from django.urls import path
from showcase.views.position_views import PositionListView
from showcase.views.position_views import PositionCreateView
from showcase.views.position_views import PositionUpdateView
from showcase.views.position_views import PositionDeleteView

urlpatterns = [
    path(
        "position/list",
        PositionListView.as_view(),
        name="position_list",
    ),
    path(
        "position/create",
        PositionCreateView.as_view(),
        name="position_create",
    ),
    path(
        "position/<int:pk>/delete",
        PositionDeleteView.as_view(),
        name="position_delete",
    ),
    path(
        "position/<int:pk>/update",
        PositionUpdateView.as_view(),
        name="position_update",
    ),
]
