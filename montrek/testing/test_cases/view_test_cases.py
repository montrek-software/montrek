import datetime
import pandas as pd
from django.test import TestCase
from django.views import View
from user.tests.factories.montrek_user_factories import MontrekUserFactory
from django.urls import reverse


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


class MontrekListViewTestCase(MontrekViewTestCase):
    pass


class MontrekCreateViewTestCase(MontrekViewTestCase):
    def creation_data(self) -> dict:
        # Method to be overwritten
        return {}

    def additional_assertions(self, created_object):
        # Method to be overwritten
        pass

    def test_view_post_success(self):
        url = reverse(self.viewname)
        data = self.creation_data()
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        # Check added data
        std_query = self.view_class().manager.repository.std_queryset()
        self.assertEqual(std_query.count(), 1)
        created_object = std_query.last()
        for key, value in data.items():
            if key.startswith("link_"):
                continue
            created_value = getattr(created_object, key)
            if isinstance(created_value, (datetime.datetime, datetime.date)):
                value = pd.to_datetime(value).date()
            self.assertEqual(created_value, value)
        self.additional_assertions(created_object)
