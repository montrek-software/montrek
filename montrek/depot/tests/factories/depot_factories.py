import factory

class DepotHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'depot.DepotHub'

class DepotSatelitteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'depot.DepotSatelitte'
    hub_entity = factory.SubFactory(DepotHubFactory)
    depot_name = factory.Sequence(lambda n: f'depot_name_{n}')
