from django.core.paginator import Paginator

from file_upload.repositories.file_upload_queries import get_upload_regisrty_files_from_account_id

def get_paginated_upload_registries(account_id, page_number=1, paginate_by=10):
    upload_registries = get_upload_regisrty_files_from_account_id(account_id)
    paginator = Paginator(upload_registries.order_by("-created_at").all(), paginate_by)
    page = paginator.get_page(page_number)
    return page
