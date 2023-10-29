import pandas as pd


from asset.models import AssetHub
from asset.models import AssetStaticSatellite
from asset.models import AssetLiquidSatellite
from account.models import AccountHub
from transaction.models import TransactionHub
from transaction.models import TransactionSatellite

ACCOUNT_ID = 8


def run():
    # Read in the data

    data_df = pd.read_csv("scripts/data/start_depot_20231029.csv")
    data_df = data_df.loc[
        ~pd.isnull(data_df["Bestand"]),
        ["Bestand", "Name", "WKN", "ISIN", "Kaufkurs Currency"],
    ]

    account = AccountHub.objects.get(id=ACCOUNT_ID)

    # Remove all assets
    AssetHub.objects.all().delete()

    # Remove all transactions

    TransactionHub.objects.filter(link_transaction_account=account).delete()

    for _, row in data_df.iterrows():
        asset_hub = AssetHub()
        asset_hub.save()
        AssetStaticSatellite(
            hub_entity=asset_hub,
            asset_name=row["Name"],
            asset_type="ETF",
        ).save()
        AssetLiquidSatellite(
            hub_entity=asset_hub,
            asset_wkn=row["WKN"],
            asset_isin=row["ISIN"],
        ).save()
        transaction_hub = TransactionHub()
        transaction_hub.save()
        transaction_hub.link_transaction_account.add(account)
        transaction_hub.link_transaction_asset.add(asset_hub)
        TransactionSatellite(
            hub_entity=transaction_hub,
            transaction_amount=row["Bestand"],
            transaction_price=row["Kaufkurs Currency"],
            transaction_date="2023-10-01",
            transaction_party="Depot Intern",
            transaction_party_iban="DE45514108000264295047",
        ).save()
