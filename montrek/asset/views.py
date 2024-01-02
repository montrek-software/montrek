from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.generic.edit import CreateView
from django.utils import timezone
from baseclasses.views import MontrekListView
from baseclasses.views import MontrekCreateView
from baseclasses.views import MontrekDetailView
from baseclasses.views import MontrekUpdateView
from baseclasses.dataclasses import table_elements
from asset.models import AssetTimeSeriesSatellite
from asset.models import AssetHub
from asset.forms import AssetTimeSeriesSatelliteForm
from asset.forms import AssetCreateForm
from asset.repositories.asset_repository import AssetRepository
from asset.pages import AssetOverviewPage
from asset.pages import AssetPage
from asset.managers.market_data import update_asset_prices_from_yf
from asset.managers.market_data import add_single_price_to_asset
from currency.managers.fx_rate_update_factory import FxRateUpdateFactory

# Create your views here.


class AssetOverview(MontrekListView):
    page_class = AssetOverviewPage
    tab = "tab_asset_list"
    title = "Asset Overview"
    repository = AssetRepository

    @property
    def elements(self) -> list:
        return (
            table_elements.LinkTextTableElement(
                name="Asset Name",
                url="asset_details",
                kwargs={"pk": "id"},
                text="asset_name",
                hover_text="View Asset",
            ),
            table_elements.StringTableElement(
                name="Asset Type",
                attr="asset_type",
            ),
            table_elements.StringTableElement(
                name="Asset ISIN",
                attr="asset_isin",
            ),
            table_elements.StringTableElement(
                name="Asset WKN",
                attr="asset_wkn",
            ),
            table_elements.StringTableElement(
                name="Currency",
                attr="ccy_code",
            ),
        )


class AssetCreateView(MontrekCreateView):
    page_class = AssetOverviewPage
    repository = AssetRepository
    title = "Asset"
    form_class = AssetCreateForm
    success_url = "asset"


class AssetDetailsView(MontrekDetailView):
    page_class = AssetPage
    repository = AssetRepository
    tab = "tab_details"
    title = "Asset Details"

    @property
    def elements(self) -> list:
        return (
            table_elements.StringTableElement(
                name="Asset Type",
                attr="asset_type",
            ),
            table_elements.StringTableElement(
                name="Asset ISIN",
                attr="asset_isin",
            ),
            table_elements.StringTableElement(
                name="Asset WKN",
                attr="asset_wkn",
            ),
            table_elements.StringTableElement(
                name="Currency",
                attr="ccy_code",
            ),
        )

class AssetUpdateView(MontrekUpdateView):
    page_class = AssetPage
    repository = AssetRepository
    title = "Asset Upudate"
    form_class = AssetCreateForm


class AssetTimeSeriesCreateView(CreateView):
    model = AssetTimeSeriesSatellite
    form_class = AssetTimeSeriesSatelliteForm
    template_name = "asset_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag"] = "Create"
        context["title"] = "Asset Time Series"
        return context

    def get_success_url(self):
        account_id = self.kwargs["account_id"]
        return reverse("bank_account_view_depot", kwargs={"account_id": account_id})

    def form_valid(self, form):
        asset_hub = AssetHub.objects.get(id=self.kwargs["asset_id"])
        add_single_price_to_asset(
            asset_hub, form.instance.price, form.instance.value_date
        )
        return HttpResponseRedirect(self.get_success_url())


def view_update_asset_prices(request, account_id: int):
    update_asset_prices_from_yf()
    fx_update_strategy = FxRateUpdateFactory.get_fx_rate_update_strategy("yahoo")
    fx_update_strategy.update_fx_rates(timezone.now())
    return HttpResponseRedirect(
        reverse("account_view_depot", kwargs={"pk": account_id})
    )
