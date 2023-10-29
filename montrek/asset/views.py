from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.generic.edit import CreateView
from asset.models import AssetStaticSatellite
from asset.models import AssetLiquidSatellite
from asset.models import AssetTimeSeriesSatellite
from asset.models import AssetHub
from asset.forms import AssetStaticSatelliteForm
from asset.forms import AssetLiquidSatelliteForm
from asset.forms import AssetTimeSeriesSatelliteForm
from asset.managers.market_data import update_asset_prices_from_yf
from asset.managers.market_data import add_single_price_to_asset

# Create your views here.

class AssetStaticCreateView(CreateView):
    model = AssetStaticSatellite
    form_class = AssetStaticSatelliteForm
    template_name = 'asset_form.html'



    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = 'Create'
        context['title'] = 'Asset Static'
        return context

    def get_success_url(self):
        asset_static_sat = self.object
        if asset_static_sat.is_liquid:
            return reverse(
                'asset_liquid_create_form',
                kwargs={'asset_hub_id': asset_static_sat.hub_entity.id,
                        'account_id': self.kwargs['account_id']})
        account_id = self.kwargs['account_id']
        return reverse('bank_account_view_transactions',
                       kwargs={'account_id': account_id})

    def form_valid(self, form):
        asset_hub = AssetHub()
        asset_hub.save()
        form.instance.hub_entity = asset_hub
        self.object = form.save()
        return HttpResponseRedirect(self.get_success_url())

class AssetLiquidCreateView(CreateView):
    model = AssetLiquidSatellite
    form_class = AssetLiquidSatelliteForm
    template_name = 'asset_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = 'Create'
        context['title'] = 'Asset Liquid'
        return context

    def get_success_url(self):
        account_id = self.kwargs['account_id']
        return reverse('transaction_add_form',
                       kwargs={'account_id': account_id})

    def form_valid(self, form):
        asset_hub = AssetHub.objects.get(id=self.kwargs['asset_hub_id'])
        form.instance.hub_entity = asset_hub
        form.save()
        return HttpResponseRedirect(self.get_success_url())

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
    return HttpResponseRedirect(
        reverse('bank_account_view_depot',
                kwargs={'account_id': account_id}))
