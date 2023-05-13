import factory

class TestMontrekHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'baseclasses.TestMontrekHub'

class TestMontrekSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'baseclasses.TestMontrekSatellite'
    test_name = factory.Sequence(lambda n: f'Test Name {n}')

class TestMontrekLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'baseclasses.TestMontrekLink'
