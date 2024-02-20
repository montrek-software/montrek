import factory


class MontrekUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "user.MontrekUser"

    email = factory.Faker("email")
    password = factory.Faker("password")
