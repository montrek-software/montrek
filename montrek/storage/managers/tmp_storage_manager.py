import tempfile
import os
import shutil
from storage.managers.base_storage_managers import BaseStorageManager


class TmpStorageManager(BaseStorageManager):
    def __init__(self):
        self.storage_path = tempfile.mkdtemp()

    def save(self, file_path: str) -> str:
        """
        Save a file to the temporary storage directory.

        :param file_path: Path to the file to be saved.
        :raises FileNotFoundError: If the provided file_path does not exist.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")

        # Copy the file to the temporary directory
        destination = os.path.join(self.storage_path, os.path.basename(file_path))
        shutil.copy(file_path, destination)
        return destination

    def load(self, file_name: str) -> bytes:
        """
        Load a file's content from the temporary storage directory.

        :param file_name: Name of the file to load.
        :return: The file's content as bytes.
        :raises FileNotFoundError: If the file does not exist in the temporary storage.
        """
        file_path = os.path.join(self.storage_path, file_name)

        if not os.path.exists(file_path):
            raise FileNotFoundError(
                f"The file {file_name} does not exist in temporary storage."
            )

        with open(file_path, "rb") as f:
            return f.read()

    def cleanup(self):
        """
        Cleanup the temporary directory and its contents.
        """
        shutil.rmtree(self.storage_path)
