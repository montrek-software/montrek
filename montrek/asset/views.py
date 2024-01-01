from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.generic.edit import CreateView
from django.utils import timezone
from baseclasses.views import MontrekListView
from baseclasses.views import MontrekCreateView
from asset.models import AssetTimeSeriesSatellite
from asset.models import AssetHub
from asset.forms import AssetTimeSeriesSatelliteForm
from asset.forms import AssetCreateForm
from asset.repositories.asset_repository import AssetRepository
from asset.pages import AssetOverviewPage
from asset.managers.market_data import update_asset_prices_from_yf
from asset.managers.market_data import add_single_price_to_asset
from currency.managers.fx_rate_update_factory import FxRateUpdateFactory

# Create your views here.

class AssetOverview(MontrekListView):
    page_class = AssetOverviewPage
    tab = "tab_asset_list"
    title = "Asset Overview"
    repository = AssetRepository

class AssetCreateView(MontrekCreateView):
    page_class = AssetOverviewPage
    repository = AssetRepository
    title = "Asset"
    form_class = AssetCreateForm
    success_url = "asset"

class AssetTimeSeriesCreateView(CreateView):
    model = AssetTimeSeriesSatellite
    form_class = AssetTimeSeriesSatelliteForm
    template_name = 'asset_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = 'Create'
        context['title'] = 'Asset Time Series'
        return context

    def get_success_url(self):
        account_id = self.kwargs['account_id']
        return reverse('bank_account_view_depot',
                       kwargs={'account_id': account_id})

    def form_valid(self, form):
        asset_hub = AssetHub.objects.get(id=self.kwargs['asset_id'])
        add_single_price_to_asset(asset_hub, form.instance.price, form.instance.value_date)
        return HttpResponseRedirect(self.get_success_url())

def view_update_asset_prices(request, account_id: int):
    update_asset_prices_from_yf()
    fx_update_strategy = FxRateUpdateFactory.get_fx_rate_update_strategy('yahoo')
    fx_update_strategy.update_fx_rates(timezone.now())
    return HttpResponseRedirect(
        reverse('account_view_depot',
                kwargs={'pk': account_id}))
