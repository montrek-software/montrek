import warnings
from django.core.paginator import UnorderedObjectListWarning

warnings.filterwarnings("ignore", category=UnorderedObjectListWarning)
