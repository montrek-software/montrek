from django.urls import path
from montrek_example import views

urlpatterns = [
    path(
        "a/create",
        views.MontrekExampleACreate.as_view(),
        name="montrek_example_a_create",
    ),
    path("a/list", views.MontrekExampleAList.as_view(), name="montrek_example_a_list"),
    path(
        "b/create",
        views.MontrekExampleBCreate.as_view(),
        name="montrek_example_b_create",
    ),
    path("b/list", views.MontrekExampleBList.as_view(), name="montrek_example_b_list"),
    path(
        "a/<int:pk>/update",
        views.MontrekExampleAUpdate.as_view(),
        name="montrek_example_a_update",
    ),
    path(
        "a/<int:pk>/details",
        views.MontrekExampleADetails.as_view(),
        name="montrek_example_a_details",
    ),
    path(
        "a/<int:pk>/delete",
        views.MontrekExampleADelete.as_view(),
        name="montrek_example_a_delete",
    ),
]
