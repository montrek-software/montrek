from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.generic.edit import CreateView
from asset.models import AssetStaticSatellite
from asset.models import AssetHub
from asset.forms import AssetStaticSatelliteForm

# Create your views here.

class AssetCreateView(CreateView):
    model = AssetStaticSatellite
    form_class = AssetStaticSatelliteForm
    template_name = 'asset_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['account_id'] = self.kwargs['account_id']
        context['tag'] = 'Create'
        return context

    def get_success_url(self):
        asset_static_sat = self.object
        if asset_static_sat.is_liquid:
            return reverse(
                'asset_liquid_create_form',
                kwargs={'asset_hub_id': asset_static_sat.hub_entity.id})
        account_id = self.kwargs['account_id']
        return reverse('bank_account_view_transactions',
                       kwargs={'account_id': account_id})

    def form_valid(self, form):
        asset_hub = AssetHub()
        asset_hub.save()
        form.instance.hub_entity = asset_hub
        self.object = form.save()
        return HttpResponseRedirect(self.get_success_url())
