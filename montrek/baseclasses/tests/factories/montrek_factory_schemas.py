import factory

from baseclasses.models import ValueDateList


class MontrekTSSatelliteFactory(factory.django.DjangoModelFactory):
    @factory.post_generation
    def value_date(self, create, extracted, **kwargs):
        if not create:
            return
        if not extracted:
            return
        value_date_list = ValueDateList.objects.filter(value_date=extracted)
        if value_date_list.count() == 1:
            value_date_list = value_date_list.first()
        else:
            value_date_list = ValueDateList.objects.create(value_date=extracted)
        self.hub_value_date.value_date_list = value_date_list
        self.hub_value_date.save()
