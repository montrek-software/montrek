from django.contrib.auth.models import Group
import factory


class GroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Group

    name = factory.Sequence(lambda n: f"group_{n}")
