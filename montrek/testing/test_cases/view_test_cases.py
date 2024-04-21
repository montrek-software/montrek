import datetime
import pandas as pd
from django.test import TestCase
from django.views import View
from django.contrib.auth.models import Permission
from user.tests.factories.montrek_user_factories import MontrekUserFactory
from django.urls import reverse


class NotImplementedView(View):
    pass


class MontrekViewTestCase(TestCase):
    viewname: str = "Please set the viewname in the subclass"
    view_class: type[View] = NotImplementedView
    user_permissions: list[str] = []

    def setUp(self):
        self._check_view_class()
        self.user = MontrekUserFactory()
        for perm in self.user_permissions:
            self.permission = Permission.objects.get(codename=perm)
            self.user.user_permissions.add(self.permission)
        self.client.force_login(self.user)
        self.build_factories()

    def _check_view_class(self):
        if self.view_class == NotImplementedView:
            raise NotImplementedError("Please set the view_class in the subclass")

    def build_factories(self):
        pass

    def url_kwargs(self) -> dict:
        return {}

    @property
    def url(self):
        return reverse(self.viewname, kwargs=self.url_kwargs())

    @property
    def response(self):
        return self.client.get(self.url)

    def test_view_return_correct_html(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertTemplateUsed(self.response, self.view_class.template_name)


class MontrekListViewTestCase(MontrekViewTestCase):
    expected_no_of_rows: int = 0

    def test_view_get_success(self):
        self.assertEqual(
            len(self.response.context["object_list"]), self.expected_no_of_rows
        )


class MontrekCreateViewTestCase(MontrekViewTestCase):
    def creation_data(self) -> dict:
        # Method to be overwritten
        return {}

    def additional_assertions(self, created_object):
        # Method to be overwritten
        pass

    def test_view_post_success(self):
        data = self.creation_data()
        post_response = self.client.post(self.url, data)
        self.assertEqual(post_response.status_code, 302)
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
