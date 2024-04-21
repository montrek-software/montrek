from django.test import TestCase
from django.views import View
from user.tests.factories.montrek_user_factories import MontrekUserFactory


class NotImplementedView(View):
    pass


class MontrekViewTestCase(TestCase):
    viewname: str = "Please set the viewname in the subclass"
    view_class: type[View] = NotImplementedView

    def setUp(self):
        self._check_view_class()
        self.user = MontrekUserFactory()
        self.client.force_login(self.user)
        self.build_factories()

    def _check_view_class(self):
        if self.view_class == NotImplementedView:
            raise NotImplementedError("Please set the view_class in the subclass")

    def build_factories(self):
        pass

    def test_view_return_correct_html(self):
        url = reverse(self.viewname)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, self.view_class.template_name)


class ListViewTestCase(MontrekViewTestCase):
    pass
