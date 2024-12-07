from .sproduct_urls import urlpatterns as sproduct_urls
from .stransaction_urls import urlpatterns as stransaction_urls
from .sposition_urls import urlpatterns as sposition_urls
from .sasset_urls import urlpatterns as sasset_urls

urlpatterns = sproduct_urls + stransaction_urls + sposition_urls + sasset_urls
