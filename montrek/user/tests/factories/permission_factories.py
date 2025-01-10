import factory
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


class ContentTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ContentType

    app_label = factory.Sequence(lambda n: f"app_{n}")
    model = factory.Sequence(lambda n: f"model_{n}")


class PermissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Permission

    name = factory.Sequence(lambda n: f"permission_{n}")
    codename = factory.Sequence(lambda n: f"codename_{n}")
    content_type = factory.SubFactory(ContentTypeFactory)
