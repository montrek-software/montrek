from django.shortcuts import render
from django.http import HttpResponseRedirect
from file_upload.forms import UploadFileForm

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
