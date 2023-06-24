from django.utils import timezone
import factory

class TestMontrekHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'baseclasses.TestMontrekHub'

class TestMontrekSatelliteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'baseclasses.TestMontrekSatellite'
    test_name = factory.Sequence(lambda n: f'Test Name {n}')
    state_date = timezone.datetime(2023,6,20, tzinfo=timezone.utc)

class TestMontrekLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'baseclasses.TestMontrekLink'
