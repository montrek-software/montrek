from .sftp_connection_urls import urlpatterns as sftp_connection_urls
from .sftp_import_source_urls import urlpatterns as sftp_import_source_urls

urlpatterns = sftp_connection_urls + sftp_import_source_urls
