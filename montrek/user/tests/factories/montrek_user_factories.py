import factory


class MontrekUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "user.MontrekUser"

    email = factory.Faker("email")
    is_active = True
    password = "S3cret!123"  # nosec B105: test-only password

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)
