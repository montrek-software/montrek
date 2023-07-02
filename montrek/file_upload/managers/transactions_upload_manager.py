from file_upload.models import FileUploadFileStaticSatellite
from file_upload.repositories.file_upload_queries import get_account_hub_from_file_upload_registry_satellite
from credit_institution.model_utils import get_credit_institution_satellite_by_account_hub

def upload_transactions_to_account_manager(
    upload_registry_sat: FileUploadFileStaticSatellite
) -> None:
    if upload_registry_sat.upload_status != 'uploaded':
        return file_not_uploaded_registry(upload_registry_sat)
    account_hub =  get_account_hub_by_file_upload_registry_satellite(
        upload_registry_sat
    )
    credit_institution_satellite = get_credit_institution_satellite_from_account_hub(
        account_hub
    )
    if credit_institution_satellite.account_upload_method == 'none':
        return account_upload_method_none(upload_registry_sat, 
            credit_institution_satellite)

def file_not_uploaded_registry(upload_registry_sat):
    fileuploadregistry_failed = update_satellite(
        upload_registry_sat,
        upload_status='failed',
        upload_message='Try to process file that has not been not uploaded',
    )
    return fileuploadregistry_failed

def account_upload_method_none(upload_registry_sat, credit_institution_satellite):
    credit_institution_name = credit_institution_satellite.credit_institution_name
    fileuploadregistry_failed = update_satellite(
        upload_registry_sat,
        upload_status='failed',
            upload_message=f'Credit Institution {credit_institution_name} provides no upload method',
    )
    return fileuploadregistry_failed
