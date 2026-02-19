from django.test import TransactionTestCase
from django.db import connection, models
from django.apps import apps
from copy import deepcopy

from baseclasses.repositories.view_model_repository import ViewModelRepository


class TestViewModelRepository(TransactionTestCase):
    """Fully isolated dynamic-model test without migration files."""

    reset_sequences = True

    @classmethod
    def _make_models(cls):
        # Use a fake app label that is NOT in INSTALLED_APPS
        # Django won't generate migrations for it
        app_label = "dynamic_test_app"

        cls.DummyHub = type(
            "DummyHub",
            (models.Model,),
            {
                "name": models.CharField(max_length=100),
                "__module__": __name__,
                "Meta": type(
                    "Meta",
                    (),
                    {
                        "app_label": app_label,
                    },
                ),
            },
        )

        cls.MockModel = type(
            "MockModel",
            (models.Model,),
            {
                "hub": models.ForeignKey(
                    cls.DummyHub,
                    on_delete=models.CASCADE,
                    related_name="mock_set",
                ),
                "__module__": __name__,
                "Meta": type(
                    "Meta",
                    (),
                    {
                        "app_label": app_label,
                    },
                ),
            },
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._make_models()
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(cls.DummyHub)
            schema_editor.create_model(cls.MockModel)
        connection.commit()

    @classmethod
    def tearDownClass(cls):
        connection.rollback()
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(cls.MockModel)
            schema_editor.delete_model(cls.DummyHub)
        connection.commit()
        super().tearDownClass()

    def test_has_view_model(self):
        view_model_repository_none = ViewModelRepository(None)
        self.assertFalse(view_model_repository_none.has_view_model())

        view_model_repository = ViewModelRepository(self.MockModel)
        self.assertTrue(view_model_repository.has_view_model())

    def test_generate_view_model_creates_valid_model(self):
        fields = {
            "test_field": models.CharField(max_length=50),
            "number": models.IntegerField(),
        }
        model_cls = ViewModelRepository.generate_view_model(
            module_name="myproject.testapp.repositories.some_repo",
            repository_name="TestRepo",
            hub_class=self.DummyHub,
            fields=deepcopy(fields),
        )

        apps.register_model("testapp", model_cls)
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(model_cls)
        connection.commit()

        hub = self.DummyHub.objects.create(name="Main Hub")
        instance = model_cls.objects.create(
            test_field="example",
            number=42,
            hub=hub,
        )
        self.assertEqual(instance.test_field, "example")

        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(model_cls)
        connection.commit()
