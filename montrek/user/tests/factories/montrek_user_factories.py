import factory


class MontrekUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "user.MontrekUser"

    email = factory.Faker("email")
    is_active = True
    password = factory.Faker("password")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for group in extracted:
                self.groups.add(group)
