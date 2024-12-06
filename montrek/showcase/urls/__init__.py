from .product_urls import urlpatterns as product_urls
from .transaction_urls import urlpatterns as transaction_urls
from .position_urls import urlpatterns as position_urls

urlpatterns = product_urls + transaction_urls + position_urls
