import factory
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


class ContentTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ContentType

    app_label = factory.Faker("word")
    model = factory.Faker("word")


class PermissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Permission

    name = factory.Faker("word")
    codename = factory.Faker("word")
    content_type = factory.SubFactory(ContentTypeFactory)
