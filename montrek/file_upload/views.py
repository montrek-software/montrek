from typing import TextIO
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.http import FileResponse
from file_upload.forms import UploadFileForm
from file_upload.managers.file_upload_manager import FileUploadManager
from baseclasses.views import MontrekTemplateView

# Create your views here.

class NotDefinedFileUploadProcessor:
    message = "File upload processor not defined"
    def process(self, file: TextIO):
        raise NotImplementedError( self.message)

class MontrekUploadFileView(MontrekTemplateView):
    template_name = "upload_transaction_to_account_form.html"
    file_upload_processor = NotDefinedFileUploadProcessor()


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = UploadFileForm()
        return context

    def post(self, request, *args, **kwargs):
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file_upload_manager = FileUploadManager(self.file_upload_processor, request.FILES["file"])
            file_upload_manager = file_upload_manager.upload_and_process()
        else:
            return self.render_to_response(self.get_context_data())


#def download_upload_file(
#    request, upload_registry_id: int
#):
#    upload_file_file_sat = get_file_satellite_from_registry_hub_id(upload_registry_id)
#    return FileResponse(upload_file_file_sat.file, as_attachment=True)
