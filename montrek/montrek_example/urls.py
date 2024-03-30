from django.urls import path
from file_upload.views import MontrekFieldMapCreate, MontrekFieldMapList
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
    path(
        "a/<int:pk>/history",
        views.MontrekExampleAHistory.as_view(),
        name="montrek_example_a_history",
    ),
    path(
        "c/list",
        views.MontrekExampleCList.as_view(),
        name="montrek_example_c_list",
    ),
    path(
        "c/create",
        views.MontrekExampleCCreate.as_view(),
        name="montrek_example_c_create",
    ),
    path(
        "d/list",
        views.MontrekExampleDList.as_view(),
        name="montrek_example_d_list",
    ),
    path(
        "d/create",
        views.MontrekExampleDCreate.as_view(),
        name="montrek_example_d_create",
    ),
    path(
        "field_map/list",
        MontrekFieldMapList.as_view(),
        name="montrek_example_field_map_list",
    ),
    path(
        "field_map/create",
        MontrekFieldMapCreate.as_view(),
        name="montrek_example_field_map_create",
    ),
    path(
        "a_upload_file",
        views.MontrekExampleAUploadFileView.as_view(),
        name="a_upload_file",
    ),
    path(
        "a_view_uploads",
        views.MontrekExampleAUploadView.as_view(),
        name="a_view_uploads",
    ),
]
