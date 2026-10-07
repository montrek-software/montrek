from django.urls import path
from baseclasses.views import MontrekNavigationRedirectView
from sftp.views.sftp_connection_views import SftpConnectionListView
from sftp.views.sftp_connection_views import SftpConnectionCreateView
from sftp.views.sftp_connection_views import SftpConnectionUpdateView
from sftp.views.sftp_connection_views import SftpConnectionDeleteView
from sftp.views.sftp_connection_views import SftpConnectionDetailView
from sftp.views.sftp_connection_views import SftpConnectionHistoryView

urlpatterns = [
    path(
        "sftp_connection",
        MontrekNavigationRedirectView.as_view(
            access_module=__name__,
            pattern_name="sftp_connection_list",
        ),
        name="sftp_connection",
    ),
    path(
        "sftp_connection/list",
        SftpConnectionListView.as_view(),
        name="sftp_connection_list",
    ),
    path(
        "sftp_connection/create",
        SftpConnectionCreateView.as_view(),
        name="sftp_connection_create",
    ),
    path(
        "sftp_connection/<int:pk>/delete",
        SftpConnectionDeleteView.as_view(),
        name="sftp_connection_delete",
    ),
    path(
        "sftp_connection/<int:pk>/update",
        SftpConnectionUpdateView.as_view(),
        name="sftp_connection_update",
    ),
    path(
        "sftp_connection/<int:pk>/details",
        SftpConnectionDetailView.as_view(),
        name="sftp_connection_details",
    ),
    path(
        "sftp_connection/<int:pk>/history",
        SftpConnectionHistoryView.as_view(),
        name="sftp_connection_history",
    ),
]
