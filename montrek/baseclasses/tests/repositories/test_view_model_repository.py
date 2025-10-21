from baseclasses.repositories.view_model_repository import ViewModelRepository
from django.test import TestCase


class MockModel: ...


class TestViewModelRepository(TestCase):
    def test_has_view_model(self):
        view_model_repository_none = ViewModelRepository(None)
        self.assertFalse(view_model_repository_none.has_view_model())
        view_model_repository = ViewModelRepository(MockModel)
        self.assertTrue(view_model_repository.has_view_model())
