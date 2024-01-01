from asset.models import AssetHub
from baseclasses.repositories.montrek_repository import MontrekRepository

class AssetRepository(MontrekRepository):
    hub_class = AssetHub

    def std_queryset(self):
        return self.build_queryset()
