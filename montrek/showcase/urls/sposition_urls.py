from django.urls import path
from showcase.views.sposition_views import SPositionListView

urlpatterns = [
    path(
        "sposition/list",
        SPositionListView.as_view(),
        name="sposition_list",
    ),
]
