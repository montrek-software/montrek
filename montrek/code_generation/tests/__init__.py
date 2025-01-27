import os

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def get_test_file_path(file_name):
    return os.path.join(TEST_DATA_DIR, file_name)
