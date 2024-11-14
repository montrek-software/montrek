import factory
import datetime
from django.utils import timezone


from baseclasses.models import ValueDateList


def get_value_date_list(value_date):
    if isinstance(value_date, datetime.datetime):
        value_date = value_date.date()
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


class MontrekTSSatelliteFactory(factory.django.DjangoModelFactory):
    value_date = factory.Maybe(
        "hub_value_date",
        factory.SelfAttribute("hub_value_date.value_date_list.value_date"),
        factory.Faker("date_time", tzinfo=datetime.timezone.utc),
    )

    @factory.post_generation
    def set_value_date(self, create, extracted, **kwargs):
        if not create:
            return
        value_date_list = get_value_date_list(self.value_date)
        self.hub_value_date.value_date_list = value_date_list
        self.hub_value_date.save()

    @factory.post_generation
    def hub_entity(self, create, extracted, **kwargs):
        if not create:
            return
        if not extracted:
            return
        self.hub_value_date.hub = extracted
        self.hub_value_date.save()


class MontrekSatelliteFactory(factory.django.DjangoModelFactory):
    @factory.post_generation
    def hub_value_date(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            return extracted
        value_date_list = get_value_date_list(None)
        hub_value_date_class = self.hub_entity.hub_value_date.field.model
        hub_value_date = hub_value_date_class.objects.filter(
            hub=self.hub_entity, value_date_list=value_date_list
        )
        if hub_value_date.count() == 1:
            hub_value_date = hub_value_date.first()
        else:
            hub_value_date = hub_value_date_class.objects.create(
                hub=self.hub_entity, value_date_list=value_date_list
            )
        return None


class MontrekHubValueDateFactory(factory.django.DjangoModelFactory):
    value_date_list = factory.SubFactory(ValueDateListFactory)

    @factory.post_generation
    def value_date(self, create, extracted, **kwargs):
        if not create:
            return
        if not extracted:
            return
        value_date_list = get_value_date_list(extracted)
        self.value_date_list = value_date_list
