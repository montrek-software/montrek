import os
import pandas as pd
from showcase.factories.sasset_hub_factories import LinkSAssetSCompanyFactory
from showcase.factories.scompany_sat_factories import SCompanyStaticSatelliteFactory
from showcase.models.sasset_sat_models import SAssetTypes
from showcase.models.scompany_hub_models import SCompanyHub
from showcase.models.stransaction_hub_models import STransactionHub
from showcase.tests import TEST_DATA_DIR


from showcase.models.sproduct_hub_models import SProductHub
from showcase.models.sasset_hub_models import SAssetHub
from showcase.factories.sproduct_sat_factories import SProductSatelliteFactory
from showcase.factories.sasset_sat_factories import SAssetStaticSatelliteFactory


class InitialDbDataGenerator:
    def __init__(self, session_data):
        self.session_data = session_data
        self.test_file_path = os.path.join(
            TEST_DATA_DIR, "stransaction_upload_file.csv"
        )
        self.test_file_data = pd.read_csv(self.test_file_path)

    def generate(self):
        self.delete_existing_data()
        self.generate_product_data()
        self.generate_asset_data()

    def delete_existing_data(self):
        SProductHub.objects.all().delete()
        SAssetHub.objects.all().delete()
        SCompanyHub.objects.all().delete()
        STransactionHub.objects.all().delete()

    def generate_product_data(self):
        product_data = self.test_file_data.groupby("product_name", as_index=False)[
            "transaction_date"
        ].min()
        product_data = product_data.rename(
            columns={"transaction_date": "inception_date"}
        )
        for row in product_data.itertuples():
            SProductSatelliteFactory(
                product_name=row.product_name, inception_date=row.inception_date
            )

    def generate_asset_data(self):
        asset_data = self.test_file_data[
            ["asset_name", "company_name", "ISIN"]
        ].drop_duplicates(subset=["ISIN"], keep="first")
        for row in asset_data.itertuples():
            asset_sat = SAssetStaticSatelliteFactory(
                asset_name=row.asset_name,
                asset_type=SAssetTypes.EQUITY.value,
                asset_isin=row.ISIN,
            )
            company_sat = SCompanyStaticSatelliteFactory(
                company_name=row.company_name,
            )
            LinkSAssetSCompanyFactory(
                hub_in=asset_sat.hub_entity, hub_out=company_sat.hub_entity
            )
