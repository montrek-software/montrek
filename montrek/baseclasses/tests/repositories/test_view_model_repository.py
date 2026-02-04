from copy import deepcopy

from baseclasses.repositories.view_model_repository import ViewModelRepository
from django.apps import apps
from django.db import connection, models
from django.test import TransactionTestCase


class MockModel(models.Model): ...


class DummyHub(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = "testapp"


class TestViewModelRepository(TransactionTestCase):
    """Fully isolated dynamic-model test without migration files."""

    reset_sequences = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create DummyHub table once
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(DummyHub)
            # schema_editor.create_model(MockModel)
        # Explicitly commit to ensure schema visible outside current atomic block
        connection.commit()

    @classmethod
    def tearDownClass(cls):
        # Drop DummyHub safely
        connection.rollback()  # clear any failed tx
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(DummyHub)
            schema_editor.delete_model(MockModel)
        connection.commit()
        super().tearDownClass()

    def test_has_view_model(self):
        view_model_repository_none = ViewModelRepository(None)
        self.assertFalse(view_model_repository_none.has_view_model())
        view_model_repository = ViewModelRepository(MockModel)
        self.assertTrue(view_model_repository.has_view_model())

    def test_generate_view_model_creates_valid_model(self):
        fields = {
            "test_field": models.CharField(max_length=50),
            "number": models.IntegerField(),
        }

        model_cls = ViewModelRepository.generate_view_model(
            module_name="myproject.testapp.repositories.some_repo",
            repository_name="TestRepo",
            hub_class=DummyHub,
            fields=deepcopy(fields),
        )

        # Register and create its table
        apps.register_model("testapp", model_cls)
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(model_cls)
        connection.commit()

        # --- ORM usage works fine now ---
        hub = DummyHub.objects.create(name="Main Hub")
        instance = model_cls.objects.create(
            test_field="example",
            number=42,
            hub=hub,
        )
        self.assertEqual(instance.test_field, "example")

        # Clean up the table (not strictly required)
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(model_cls)
        connection.commit()
