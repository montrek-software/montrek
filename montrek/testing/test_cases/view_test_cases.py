import datetime
from django.db.models import QuerySet
from django.http import FileResponse
import pandas as pd
from django.test import TestCase
from django.views import View
from django.contrib.auth.models import Permission
from user.tests.factories.montrek_user_factories import MontrekUserFactory
from django.urls import reverse
from bs4 import BeautifulSoup
from baseclasses.views import MontrekDeleteView


class NotImplementedView(View):
    pass


class MontrekViewTestCase(TestCase):
    viewname: str = "Please set the viewname in the subclass"
    view_class: type[View] = NotImplementedView
    expected_status_code: int = 200

    def setUp(self):
        if self._is_base_test_class():
            return
        self._check_view_class()
        self.build_factories()
        self._login_user()
        self.response = self.get_response()
        self.view = self.response.context.get("view")

    def _check_view_class(self):
        if self.view_class == NotImplementedView:
            raise NotImplementedError(
                f"{self.__class__.__name__}: Please set the view_class"
            )

    def _login_user(self):
        self.user = MontrekUserFactory()
        self.client.force_login(self.user)
        self.user.user_permissions.set(self.user_permissions())

    def _is_base_test_class(self) -> bool:
        # Django runs all tests within these base classes here individually. This is not wanted and hence we skip the tests if django attempts to do this.
        return self.__class__.__name__ == "MontrekViewTestCase"

    def build_factories(self):
        pass

    def url_kwargs(self) -> dict:
        return {}

    def user_permissions(self) -> list[Permission]:
        return []

    @property
    def url(self):
        return reverse(self.viewname, kwargs=self.url_kwargs())

    def get_response(self):
        return self.client.get(self.url)

    def test_view_return_correct_html(self):
        if self._is_base_test_class():
            return
        self.assertEqual(self.response.status_code, self.expected_status_code)
        self.assertTemplateUsed(self.response, self.view_class.template_name)

    def test_view_page(self):
        if self._is_base_test_class():
            return
        page_context = self.view.get_page_context({})
        self.assertNotEqual(page_context["page_title"], "page_title not set!")
        self.assertNotEqual(page_context["title"], "No Title set!")

    def test_context_data(self):
        if self._is_base_test_class():
            return
        if isinstance(self.view, MontrekDeleteView):
            return
        self.assertIsInstance(self.view, self.view_class)


class MontrekListViewTestCase(MontrekViewTestCase):
    expected_no_of_rows: int = 0
    expected_columns = []

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
        bs = BeautifulSoup(self.response.context["table"], features="html.parser")
        columns = bs.find_all("th")
        for expected_column in self.expected_columns:
            self.assertIn(expected_column, [column.text for column in columns])


class MontrekObjectViewBaseTestCase(MontrekViewTestCase):
    def creation_data(self) -> dict:
        # Method to be overwritten
        return {}

    def additional_assertions(self, created_object):
        # Method to be overwritten
        pass

    def receive(self) -> QuerySet:
        return self.view.manager.repository.receive()

    def get_post_response(self):
        return self.client.post(self.url, self.creation_data())

    def _pre_test_view_post_success(self) -> bool:
        if self._is_base_test_class():
            return False
        post_response = self.get_post_response()
        self.assertEqual(post_response.status_code, 302)
        return True


class MontrekCreateUpdateViewTestCase(MontrekObjectViewBaseTestCase):
    def _is_base_test_class(self) -> bool:
        return self.__class__.__name__ == "MontrekCreateUpdateViewTestCase"

    def test_view_post_success(self):
        if not self._pre_test_view_post_success():
            return
        # Check added data
        created_object = self._get_object()
        data = self.creation_data()
        for key, value in data.items():
            if key.startswith("link_"):
                continue
            if key == "hub_entity_id":
                key = "hub_id"
            created_value = getattr(created_object, key)
            if created_value is None:
                self.assertEqual(value, "")
                continue
            if isinstance(created_value, (datetime.datetime, datetime.date)):
                value = pd.to_datetime(value).date()
                if isinstance(created_value, datetime.datetime):
                    expected_value = created_value.date()
                else:
                    expected_value = created_value
            else:
                expected_value = created_value
            self.assertEqual(expected_value, value)
        self.additional_assertions(created_object)


class GetObjectLastMixin:
    def _get_object(self) -> QuerySet:
        std_query = self.receive()
        return std_query.last()


class GetObjectPkMixin:
    def _get_object(self) -> QuerySet:
        std_query = self.receive()
        return std_query.get(pk=self.url_kwargs()["pk"])


class MontrekDetailViewTestCase(MontrekObjectViewBaseTestCase, GetObjectPkMixin):
    def _is_base_test_class(self) -> bool:
        return self.__class__.__name__ == "MontrekDetailViewTestCase"

    def test_view_get_success(self):
        if self._is_base_test_class():
            return
        context_data = self.response.context
        self.assertIsNotNone(context_data["object"])


class MontrekCreateViewTestCase(MontrekCreateUpdateViewTestCase, GetObjectLastMixin):
    def _is_base_test_class(self) -> bool:
        return self.__class__.__name__ == "MontrekCreateViewTestCase"


class MontrekUpdateViewTestCase(MontrekCreateUpdateViewTestCase, GetObjectPkMixin):
    def creation_data(self) -> dict:
        obj = self._get_object()
        data_dict = self.view.manager.repository.object_to_dict(obj)
        data_dict = {
            key: value for key, value in data_dict.items() if value is not None
        }
        data_dict.update(self.update_data())
        return data_dict

    def _is_base_test_class(self) -> bool:
        return self.__class__.__name__ == "MontrekUpdateViewTestCase"

    def update_data(self) -> dict:
        # Method to be overwritten
        return {}


class MontrekDeleteViewTestCase(MontrekObjectViewBaseTestCase, GetObjectPkMixin):
    def _is_base_test_class(self):
        return self.__class__.__name__ == "MontrekDeleteViewTestCase"

    def _get_object(self):
        std_query = self.receive()
        return std_query.filter(pk=self.url_kwargs()["pk"])

    def creation_data(self) -> dict:
        return {"action": "Delete"}

    def test_view_post_success(self):
        if not self._pre_test_view_post_success():
            return
        # Check deleted data has an end date
        query = self._get_object()
        self.assertEqual(query.count(), 0)


class MontrekFileResponseTestCase(MontrekViewTestCase):
    def _is_base_test_class(self) -> bool:
        # Django runs all tests within these base classes here individually. This is not wanted and hence we skip the tests if django attempts to do this.
        return self.__class__.__name__ == "MontrekFileResponseTestCase"

    def get_response(self):
        response = self.client.get(self.url, follow=True)
        response.context = {"view": None}
        return response

    def test_view_return_correct_html(self):
        if self._is_base_test_class():
            return
        self.assertEqual(self.response.status_code, self.expected_status_code)
        self.assertIsInstance(self.response, FileResponse)

    def test_context_data(self):
        return

    def test_view_page(self):
        return


class MontrekRestApiViewTestCase(MontrekViewTestCase):
    def _is_base_test_class(self) -> bool:
        return self.__class__.__name__ == "MontrekRestApiViewTestCase"

    def test_view_page(self):
        return

    def test_context_data(self):
        return

    def test_view_return_correct_html(self):
        if self._is_base_test_class():
            return
        self.assertEqual(self.response.status_code, self.expected_status_code)

    def test_get_return(self):
        if self._is_base_test_class():
            return
        return_json = self.response.json()
        self.assertIsInstance(return_json, list)
        self.assertEqual(return_json, self.expected_json())

    def expected_json(self) -> list:
        raise NotImplementedError("Please set the expected_json method in the subclass")


class MontrekRedirectViewTestCase(MontrekViewTestCase):
    expected_status_code: int = 302

    def _is_base_test_class(self) -> bool:
        return self.__class__.__name__ == "MontrekRedirectViewTestCase"

    def test_view_page(self):
        return

    def test_context_data(self):
        return

    def test_view_return_correct_html(self):
        if self._is_base_test_class():
            return
        self.assertEqual(self.response.status_code, self.expected_status_code)
        self.assertEqual(self.response.url, self.expected_url())

    def expected_url(self) -> str:
        raise NotImplementedError("Please set the expected_url method in the subclass")
