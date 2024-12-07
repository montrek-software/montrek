from enum import Enum
from django.db import models

from baseclasses.models import MontrekSatelliteABC
from showcase.models.sasset_hub_models import SAssetHub


class SAssetTypes(Enum):
    BOND = "BOND"
    CASH = "CASH"
    EQUITY = "EQUITY"
    FUND = "FUND"
    REAL_ESTATE = "REAL_ESTATE"

    @classmethod
    def get_choices(cls):
        return tuple((i.name, i.value) for i in cls)


class SAssetTypeSatellite(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(SAssetHub, on_delete=models.CASCADE)
    asset_type = models.CharField(max_length=255, choices=SAssetTypes.get_choices())


class SAssetStaticSatellite(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(SAssetHub, on_delete=models.CASCADE)
    asset_name = models.CharField(max_length=255)
