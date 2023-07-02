from typing import TextIO
from django.shortcuts import render
from django.http import HttpResponseRedirect
from file_upload.forms import UploadFileForm
from file_upload.models import FileUploadRegistryHub
from file_upload.models import FileUploadRegistryStaticSatellite
from file_upload.models import FileUploadFileStaticSatellite
from file_upload.models import FileUploadFileHub
from link_tables.models import FileUploadRegistryFileUploadFileLink
from baseclasses.model_utils import update_satellite
from baseclasses.model_utils import new_link_entry

from account.models import AccountHub
from credit_institution.model_utils import get_credit_institution_satellite_by_account_hub_id
from file_upload.managers.transactions_upload_manager import process_upload_transaction_file 

# Create your views here.

def upload_transaction_to_account_file(request, account_id:int):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            upload_registry = process_upload_transaction_file(
                account_id,
                request.FILES['file'],
            )
            return upload_file_message(request, upload_registry)
    else:
        form = UploadFileForm()
    return render(request, 'upload_transaction_to_account_form.html', {'form': form})

def upload_file_message(request, fileuploadregistry: FileUploadRegistryStaticSatellite):
    return render(request, 'upload_file_message.html', {'fileuploadregistry': fileuploadregistry})

