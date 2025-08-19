import datetime

import pandas as pd
from baseclasses.views import MontrekDeleteView
from bs4 import BeautifulSoup
from django.contrib.auth.models import Permission
from django.db.models import QuerySet
from django.http import FileResponse
from django.test import TestCase
from django.urls import reverse
from django.views import View
from mailing.repositories.mailing_repository import MailingRepository
from middleware.permission_error_middleware import MISSING_PERMISSION_MESSAGE
from user.tests.factories.montrek_user_factories import MontrekUserFactory

TEST_USER_PASSWORD = "S3cret!123"  # nosec B105: test-only password


class NotImplementedView(View):
    pass


class RestApiTestCaseMixin:
    def get_headers(self) -> dict[str, str]:
        get_token_url = reverse("token_obtain_pair")
        payload = {"email": self.user.email, "password": TEST_USER_PASSWORD}
        resp = self.client.post(get_token_url, payload)
        self.assertEqual(resp.status_code, 200, resp.content)
        access = resp.data["access"]
        return {"Authorization": f"Bearer {access}"}

    def rest_api_view_test(self):
        if self._is_base_test_class():
            return
        query_params = self.query_params()
        query_params.update({"gen_rest_api": "true"})
        response = self.client.get(
            self.url,
            query_params=query_params,
            headers=self.get_headers(),
        )
        response_json = response.json()
        self.view._session_data = None
        manager = self.view.manager_class(self.view.session_data)

        self.assertEqual(response_json, manager.to_json())


class MontrekViewTestCase(TestCase):
    viewname: str = "Please set the viewname in the subclass"
    view_class: type[View] = NotImplementedView
    expected_status_code: int = 200

    def setUp(self):
        if self._is_base_test_class():
            return
        self._check_view_class()
        self.build_factories()
        self.store_in_view_model()
        self._login_user()
        self.response = self.get_response()
        self.view = self.response.context.get("view")

    def _check_view_class(self):
        if self.view_class == NotImplementedView:
            raise NotImplementedError(
                f"{self.__class__.__name__}: Please set the view_class"
            )

    def _login_user(self):
        self.user = MontrekUserFactory(password=TEST_USER_PASSWORD)
        self.client.force_login(self.user)
        self.user.user_permissions.set(self.required_user_permissions())

    def _is_base_test_class(self) -> bool:
        # Django runs all tests within these base classes here individually. This is not wanted and hence we skip the tests if django attempts to do this.
        return self.__class__.__name__ == "MontrekViewTestCase"

    def build_factories(self):
        pass

    def store_in_view_model(self):
        repository_class = self.view_class.manager_class.repository_class
        if repository_class.view_model:
            repository_class({}).store_in_view_model()

    def url_kwargs(self) -> dict:
        return {}

    def query_params(self) -> dict:
        return {}

    def required_user_permissions(self) -> list[Permission]:
        return []

    @property
    def url(self):
        return reverse(self.viewname, kwargs=self.url_kwargs())

    def get_response(self):
        return self.client.get(self.url, query_params=self.query_params())

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

    def test_view_without_required_permission(self):
        if self._is_base_test_class():
            return
        required_user_permissions = self.required_user_permissions()
        if not required_user_permissions:
            return
        self.user.user_permissions.clear()
        previous_url = reverse("home")
        response = self.client.get(self.url, HTTP_REFERER=previous_url, follow=True)
        messages = list(response.context["messages"])
        self.assertRedirects(response, previous_url)
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            messages[0].message,
            MISSING_PERMISSION_MESSAGE,
        )
        self.user.user_permissions.set(required_user_permissions)


class MontrekListViewTestCase(MontrekViewTestCase, RestApiTestCaseMixin):
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

    def test_rest_api_view(self):
        self.rest_api_view_test()


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


class MontrekDetailViewTestCase(
    MontrekObjectViewBaseTestCase, GetObjectPkMixin, RestApiTestCaseMixin
):
    def _is_base_test_class(self) -> bool:
        return self.__class__.__name__ == "MontrekDetailViewTestCase"

    def test_view_get_success(self):
        if self._is_base_test_class():
            return
        context_data = self.response.context
        self.assertIsNotNone(context_data["object"])

    def test_rest_api_view(self):
        self.rest_api_view_test()


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


class MontrekDownloadViewTestCase(MontrekViewTestCase):
    def _is_base_test_class(self) -> bool:
        # Django runs all tests within these base classes here individually. This is not wanted and hence we skip the tests if django attempts to do this.
        return self.__class__.__name__ == "MontrekDownloadViewTestCase"

    def get_response(self):
        response = self.client.get(self.url, follow=True)
        response.context = {"view": None}
        return response

    def test_view_return_correct_html(self):
        if self._is_base_test_class():
            return
        self.assertEqual(self.response.status_code, self.expected_status_code)
        content_disposition = self.response.get("Content-Disposition")
        self.assertIsNotNone(content_disposition)
        self.assertRegex(
            content_disposition, f'attachment; filename="{self.expected_filename()}"'
        )
        self.additional_download_assertions()

    def expected_filename(self) -> str:
        raise NotImplementedError(
            "Please set the expected_filename method in the subclass"
        )

    def additional_download_assertions(self):
        return

    def test_context_data(self):
        return

    def test_view_page(self):
        return


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


class MontrekRestApiViewTestCase(MontrekViewTestCase, RestApiTestCaseMixin):
    def _is_base_test_class(self) -> bool:
        return self.__class__.__name__ == "MontrekRestApiViewTestCase"

    def get_response(self):
        query_params = self.query_params()
        return self.client.get(
            self.url, query_params=query_params, headers=self.get_headers(), follow=True
        )

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
        expected_json = self.expected_json()
        if expected_json is None:
            expected_json = self.manager_json()
        self.assertEqual(return_json, expected_json)

    def manager_json(self) -> list:
        view = self.view_class()
        view._session_data = None
        manager = view.manager_class({})
        return manager.to_json()

    def expected_json(self) -> list | None:
        return None


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


class MontrekReportViewTestCase(MontrekViewTestCase, RestApiTestCaseMixin):
    expected_number_of_report_elements: int = -1

    @property
    def mail_success_url(self) -> str:
        last_mail = MailingRepository({}).receive().last()
        mail_kwargs = {"pk": last_mail.pk}
        report_manager = self.view.manager
        mail_kwargs.update(report_manager.get_mail_kwargs())
        return reverse(report_manager.send_mail_url, kwargs=mail_kwargs)

    def _is_base_test_class(self) -> bool:
        return self.__class__.__name__ == "MontrekReportViewTestCase"

    def test_send_report_per_mail(self):
        if self._is_base_test_class():
            return
        user = MontrekUserFactory()
        self.client.force_login(user)
        response = self.client.get(self.url + "?send_mail=true")
        self.assertRedirects(response, self.mail_success_url)

    def test_report_content(self):
        if self._is_base_test_class():
            return
        report_manager = self.view.manager
        report_manager.collect_report_elements()
        self.assertEqual(
            len(report_manager.report_elements), self.expected_number_of_report_elements
        )

    def test_rest_api_view(self):
        self.rest_api_view_test()


class MontrekReportFieldEditViewTestCase(MontrekObjectViewBaseTestCase):
    expected_status_code = 302
    update_field = ""
    updated_content = ""

    def _is_base_test_class(self) -> bool:
        return self.__class__.__name__ == "MontrekReportFieldEditViewTestCase"

    @property
    def url(self):
        return (
            reverse(self.viewname, kwargs=self.url_kwargs())
            + f"?field={self.update_field}"
        )

    def creation_data(self) -> dict:
        return {
            "content": self.updated_content,
            "field": self.update_field,
            self.update_field: self.updated_content,
        }

    def test_view_post(self):
        if self._is_base_test_class():
            return
        self.get_post_response()
        pk = self.url_kwargs()["pk"]
        test_object = (
            self.view_class.manager_class(self.url_kwargs())
            .repository.receive()
            .get(pk=pk)
        )
        self.assertEqual(getattr(test_object, self.update_field), self.updated_content)
        self.additional_assertions(test_object)

    def test_view_post_cancel(self):
        if self._is_base_test_class():
            return
        post_data = self.creation_data().copy()
        post_data["action"] = "cancel"
        self.client.post(self.url, post_data)
        pk = self.url_kwargs()["pk"]
        test_object = (
            self.view_class.manager_class(self.url_kwargs())
            .repository.receive()
            .get(pk=pk)
        )
        self.assertNotEqual(
            getattr(test_object, self.update_field), self.updated_content
        )
        self.additional_assertions(test_object)

    def test_view_page(self): ...

    def test_view_return_correct_html(self): ...

    def test_context_data(self): ...
