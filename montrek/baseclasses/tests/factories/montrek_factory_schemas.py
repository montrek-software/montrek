import factory
import datetime
from django.utils import timezone


from baseclasses.models import ValueDateList


def value_date_to_date(value_date):
    if isinstance(value_date, datetime.datetime):
        return value_date.date()
    return value_date


def get_value_date_list(value_date):
    value_date = value_date_to_date(value_date)
    value_date_list = ValueDateList.objects.filter(value_date=value_date)
    if value_date_list.exists():
        value_date_list = value_date_list.first()
    else:
        value_date_list = ValueDateListFactory.create(value_date=value_date)
    return value_date_list


class ValueDateListFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "baseclasses.ValueDateList"

    value_date = factory.Sequence(
        lambda n: timezone.datetime(2023, 1, 1) + datetime.timedelta(days=n)
    )


class MontrekHubValueDateFactory(factory.django.DjangoModelFactory):
    value_date_list = factory.SubFactory(ValueDateListFactory)

    @factory.post_generation
    def value_date(self, create, extracted, **kwargs):
        if not create:
            return  # pragma: no cover
        if not extracted:
            return  # pragma: no cover
        extracted = None if extracted == "None" else extracted
        value_date_list = get_value_date_list(extracted)
        self.value_date_list = value_date_list


class MontrekHubFactory(factory.django.DjangoModelFactory):
    @factory.post_generation
    def set_hub_value_date(self, create, extracted, **kwargs):
        if not create:
            return  # pragma: no cover
        if extracted:
            return  # pragma: no cover
        value_date_list = get_value_date_list(None)
        hub_value_date_class = self.hub_value_date.field.model
        hub_value_date = hub_value_date_class.objects.filter(
            hub=self, value_date_list=value_date_list
        )
        if hub_value_date.count() == 1:
            hub_value_date = hub_value_date.first() # pragma: no cover
        else:
            hub_value_date = hub_value_date_class.objects.create(
                hub=self, value_date_list=value_date_list
            )
        self.hub_value_date.add(hub_value_date)


class MontrekTSSatelliteFactory(factory.django.DjangoModelFactory):
    value_date = factory.Maybe(
        "hub_value_date",
        factory.SelfAttribute("hub_value_date.value_date_list.value_date"),
        factory.Faker("date_time", tzinfo=datetime.timezone.utc),
    )

    @factory.post_generation
    def set_value_date(self, create, extracted, **kwargs):
        if not create:
            return # pragma: no cover
        value_date_list = get_value_date_list(self.value_date)
        self.hub_value_date.value_date_list = value_date_list
        self.hub_value_date.save()

    @factory.post_generation
    def hub_entity(self, create, extracted, **kwargs):
        if not create:
            return # pragma: no cover
        if not extracted:
            return # pragma: no cover
        self.hub_value_date.hub = extracted # pragma: no cover
        self.hub_value_date.save() # pragma: no cover

    @factory.post_generation
    def post(self, create, extracted, **kwargs):
        self.value_date = value_date_to_date(self.value_date)
        self.get_hash_value


class MontrekSatelliteFactory(factory.django.DjangoModelFactory):
    ...
