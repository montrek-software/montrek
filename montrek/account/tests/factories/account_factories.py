import factory


class AccountHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "account.AccountHub"


class AccountStaticSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "account.AccountStaticSatellite"

    hub_entity = factory.SubFactory(AccountHubFactory)
    account_name = factory.Sequence(lambda n: f"Account {n}")


class BankAccountPropertySatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "account.BankAccountPropertySatellite"

    hub_entity = factory.SubFactory(AccountHubFactory)


class BankAccountStaticSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "account.BankAccountStaticSatellite"

    hub_entity = factory.SubFactory(AccountHubFactory)
