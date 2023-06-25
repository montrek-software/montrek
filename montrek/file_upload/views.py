from typing import TextIO
from django.shortcuts import render
from django.http import HttpResponseRedirect
from file_upload.forms import UploadFileForm
from file_upload.models import FileUploadRegistryStaticSatellite
from file_upload.models import FileUploadFileStaticSatellite
from file_upload.models import FileUploadFileHub

from account.models import AccountHub

# Create your views here.

def upload_transaction_to_account_file(request, account_id:int, credit_institution_id:int):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            # handle_uploaded_file(request.FILES['file'])
            return HttpResponseRedirect('/success/url/')
    else:
        form = UploadFileForm()
    return render(request, 'upload_transaction_to_account_form.html', {'form': form})

def init_file_upload_registry(file: TextIO,
                              account_hub_entity: AccountHub) -> FileUploadRegistryStaticSatellite:
    pass

def upload_file(file: TextIO) -> FileUploadFileStaticSatellite:
    fileuploadhub = FileUploadFileHub.objects.create()
    fileuploadstaticsatellite = FileUploadFileStaticSatellite.objects.create(
        hub_entity = fileuploadhub,
        file=file,
    )
    return fileuploadstaticsatellite
