import factory
import datetime

from baseclasses.models import ValueDateList


def get_value_date_list(value_date):
    value_date_list = ValueDateList.objects.filter(value_date=value_date)
    if value_date_list.count() == 1:
        value_date_list = value_date_list.first()
    else:
        value_date_list = ValueDateList.objects.create(value_date=value_date)
    return value_date_list


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


class MontrekSatelliteFactory(factory.django.DjangoModelFactory):
    @factory.post_generation
    def hub_value_date(self, create, extracted, **kwargs):
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
