from django.urls import path
from showcase.views.sposition_views import SPositionListView
from showcase.views.sposition_views import SPositionCreateView
from showcase.views.sposition_views import SPositionUpdateView
from showcase.views.sposition_views import SPositionDeleteView

urlpatterns = [
    path(
        "sposition/list",
        SPositionListView.as_view(),
        name="sposition_list",
    ),
    path(
        "sposition/create",
        SPositionCreateView.as_view(),
        name="sposition_create",
    ),
    path(
        "sposition/<int:pk>/delete",
        SPositionDeleteView.as_view(),
        name="sposition_delete",
    ),
    path(
        "sposition/<int:pk>/update",
        SPositionUpdateView.as_view(),
        name="sposition_update",
    ),
]
