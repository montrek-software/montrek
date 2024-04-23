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
        if self._is_base_test_class():
            return
        self._check_view_class()
        self.user = MontrekUserFactory()
        for perm in self.user_permissions:
            self.permission = Permission.objects.get(codename=perm)
            self.user.user_permissions.add(self.permission)
        self.client.force_login(self.user)
        self.build_factories()

    def _check_view_class(self):
        if self.view_class == NotImplementedView:
            raise NotImplementedError(
                f"{self.__class__.__name__}: Please set the view_class"
            )

    def _is_base_test_class(self):
        # Django runs all tests within these base classes here individually. This is not wanted and hence we skip the tests if django attempts to do this.
        return self.__class__.__name__ == "MontrekViewTestCase"

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
        if self._is_base_test_class():
            return
        self.assertEqual(self.response.status_code, 200)
        self.assertTemplateUsed(self.response, self.view_class.template_name)


class MontrekListViewTestCase(MontrekViewTestCase):
    expected_no_of_rows: int = 0

    def _is_base_test_class(self):
        return self.__class__.__name__ == "MontrekListViewTestCase"

    def test_view_get_success(self):
        if self._is_base_test_class():
            return
        len_object_list = len(self.response.context["object_list"])
        if len_object_list == 0:
            raise NotImplementedError(
                "Define objects to show in 'build_factories()' method and set 'expected_no_of_rows' attribute"
            )
        self.assertEqual(len_object_list, self.expected_no_of_rows)


class MontrekCreateViewTestCase(MontrekViewTestCase):
    def creation_data(self) -> dict:
        # Method to be overwritten
        return {}

    def additional_assertions(self, created_object):
        # Method to be overwritten
        pass

    def _is_base_test_class(self):
        return self.__class__.__name__ == "MontrekCreateViewTestCase"

    def test_view_post_success(self):
        if self._is_base_test_class():
            return
        data = self.creation_data()
        try:
            post_response = self.client.post(self.url, data)
        except AttributeError:
            raise NotImplementedError(
                "MontrekCreateViewTestCase: Please set the creation_data method in the subclass"
            )
        self.assertEqual(post_response.status_code, 302)
        # Check added data
        std_query = self.view_class().manager.repository.std_queryset()
        self.assertEqual(std_query.count(), 1)
        created_object = std_query.last()
        for key, value in data.items():
            if key.startswith("link_"):
                continue
            created_value = getattr(created_object, key)
            if created_value is None:
                self.assertEqual(value, "")
                continue
            if isinstance(created_value, (datetime.datetime, datetime.date)):
                value = pd.to_datetime(value).date()
            self.assertEqual(created_value, value)
        self.additional_assertions(created_object)
