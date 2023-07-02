from file_upload.models import FileUploadFileStaticSatellite
from file_upload.repositories.file_upload_queries import get_account_hub_from_file_upload_registry_satellite
from credit_institution.model_utils import get_credit_institution_satellite_by_account_hub
from baseclasses.model_utils import update_satellite

def upload_transactions_to_account_manager(
    upload_registry_sat: FileUploadFileStaticSatellite
) -> None:
    if upload_registry_sat.upload_status != 'uploaded':
        return upload_error_file_not_uploaded_registry(upload_registry_sat)
    account_hub =  get_account_hub_from_file_upload_registry_satellite(
        upload_registry_sat
    )
    credit_institution_satellite = get_credit_institution_satellite_by_account_hub(
        account_hub
    )
    if credit_institution_satellite.account_upload_method == 'none':
        return upload_error_account_upload_method_none(upload_registry_sat, 
            credit_institution_satellite)
    raise NotImplementedError('Upload mechanism not implemented yet')

def upload_error_file_not_uploaded_registry(upload_registry_sat):
    fileuploadregistry_failed = update_satellite(
        upload_registry_sat,
        upload_status='failed',
        upload_message=f'File {upload_registry_sat.file_name} has not been not uploaded',
    )
    return fileuploadregistry_failed

def upload_error_account_upload_method_none(upload_registry_sat, credit_institution_satellite):
    credit_institution_name = credit_institution_satellite.credit_institution_name
    fileuploadregistry_failed = update_satellite(
        upload_registry_sat,
        upload_status='failed',
        upload_message=f'Credit Institution {credit_institution_name} provides no upload method',
    )
    return fileuploadregistry_failed
