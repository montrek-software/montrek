class NotImplementedFileUploadProcessor:
    message = "Not implemented"

    def process(self, file_path: str, file_upload_registry_hub) -> bool:
        return False

    def pre_check(self, file_path: str) -> bool:
        return False

    def post_check(self, file_path: str) -> bool:
        return False
