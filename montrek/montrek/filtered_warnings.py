import warnings
from django.core.paginator import UnorderedObjectListWarning


def add_filtered_warnings():
    warnings.filterwarnings("ignore", category=UnorderedObjectListWarning)
