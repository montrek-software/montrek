import os

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        self.model_in: str = ""
        self.model_out: str = ""
        self.path_in: str = ""
        self.path_out: str = ""
        super().__init__(stdout, stderr, no_color, force_color)

    def add_arguments(self, parser):
        parser.add_argument(
            "path_in",
            type=str,
            help="Path to app in which hub_in is located.",
        )
        parser.add_argument(
            "model_in",
            type=str,
            help="Model in in lowercase notation",
        )
        parser.add_argument(
            "path_out",
            type=str,
            help="Path to app in which hub_out is located.",
        )
        parser.add_argument(
            "model_out",
            type=str,
            help="Model out in lowercase notation",
        )

    def handle(self, *args, **kwargs):
        self.model_out = kwargs["model_out"]
        self.model_in = kwargs["model_in"]
        self.model_in_name = self.get_model_name(self.model_in)
        self.model_out_name = self.get_model_name(self.model_out)
        self.path_in = kwargs["path_in"]
        self.path_out = kwargs["path_out"]
        self.python_path_in = self.get_python_path(self.path_in)
        self.python_path_out = self.get_python_path(self.path_out)
        call_command(
            "generate_link", self.path_in, self.model_in, self.path_out, self.model_out
        )
        self.add_view_test()
        self.add_view()
        self.add_manager()
        self.add_repository()
        self.add_urls()

    def get_model_name(self, model: str) -> str:
        return model.replace("_", " ").title().replace(" ", "")

    def get_python_path(self, path: str) -> str:
        if path.endswith(os.path.sep):
            path = path[:-1]

        return path.replace(os.path.sep, ".")

    def _add_code(
        self,
        path: str,
        search_string: str,
        code: str,
        import_statements: tuple[str, ...] = (),
    ):
        with open(path, "r") as f:
            old_code = f.read()
        if search_string in old_code:
            self.stdout.write(f"{search_string} exists already in {path}!")
            return
        new_code = old_code + code
        new_code = "\n".join(import_statements) + "\n" + new_code
        with open(path, "w") as f:
            f.write(new_code)
        self.stdout.write(f"Created {search_string} in {path}!")

    def add_view_test(self):
        test_path = os.path.join(
            self.path_out, "tests", "views", f"test_{self.model_out}_views.py"
        )
        class_name = f"Test{self.model_out_name}{self.model_in_name}sListView"
        code = f"""class {class_name}(MontrekListViewTestCase):
    viewname = "{self.model_out}_{self.model_in}s_list"
    view_class = {self.model_out_name}{self.model_in_name}sListView
    expected_no_of_rows = 5

    def build_factories(self):
        self.{self.model_out}_factory = {self.model_out_name}SatelliteFactory.create()
        {self.model_in_name}SatelliteFactory.create_batch(
            5, {self.model_out}=self.{self.model_out}_factory
        )
        other_{self.model_out}_factory = {self.model_out_name}SatelliteFactory.create()
        {self.model_in_name}SatelliteFactory.create_batch(
            5, {self.model_out}=other_{self.model_out}_factory
        )

    def url_kwargs(self):
        return {{"pk": self.{self.model_out}_factory.get_hub_value_date().pk}}"""
        import_statements = (
            f"from {self.python_path_out}.views.{self.model_out}_views import {self.model_out_name}{self.model_in_name}sListView",
            f"from {self.python_path_out}.tests.factories.{self.model_out}_sat_factories import {self.model_out_name}SatelliteFactory",
            f"from {self.python_path_in}.tests.factories.{self.model_in}_sat_factories import {self.model_in_name}SatelliteFactory",
        )
        self._add_code(test_path, class_name, code, import_statements)

    def add_view(self):
        view_path = os.path.join(self.path_out, "views", f"{self.model_out}_views.py")
        class_name = f"{self.model_out_name}{self.model_in_name}sListView"
        code = f"""class {class_name}(MontrekListView):
    manager_class = {self.model_out_name}{self.model_in_name}sTableManager
    page_class = {self.model_out_name}DetailsPage
    title = "{self.model_out_name} {self.model_in_name}s"
    tab = "tab_{self.model_out}_{self.model_in}s"

    @property
    def actions(self) -> tuple[ActionElement]:
        action_create = CreateActionElement(
            url_name = "{self.model_out}_{self.model_in}_create",
            kwargs = {{"pk": self.kwargs["pk"]}},
            action_id="id_{self.model_in}_{self.model_out}_create",
            hover_text="Create {self.model_in_name} from {self.model_out_name}",
        )
        return (action_create,)


class {self.model_out_name}{self.model_in_name}CreateView({self.model_in_name}CreateView):

    def get_success_url(self):
        return reverse("{self.model_out}_{self.model_in}s_list", kwargs={{"pk": self.kwargs["pk"]}})

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        hub = {self.model_out_name}Repository(self.session_data).receive().get(hub__pk=self.kwargs["pk"])
        form["link_{self.model_in}_{self.model_out}"].initial = hub
        return form
                """
        import_statements = (
            f"from {self.python_path_out}.managers.{self.model_out}_managers import {self.model_out_name}{self.model_in_name}sTableManager",
            f"from {self.python_path_out}.repositories.{self.model_out}_repositories import {self.model_out_name}Repository",
            f"from {self.python_path_in}.views.{self.model_in}_views import {self.model_in_name}CreateView",
            "from baseclasses.dataclasses.view_classes import CreateActionElement",
        )
        self._add_code(view_path, class_name, code, import_statements)

    def add_manager(self):
        manager_path = os.path.join(
            self.path_out, "managers", f"{self.model_out}_managers.py"
        )
        class_name = f"{self.model_out_name}{self.model_in_name}sTableManager"
        code = f"""class {class_name}({self.model_in_name}TableManager):
    repository_class = {self.model_out_name}{self.model_in_name}sRepository
    """
        import_statements = (
            f"from {self.python_path_out}.repositories.{self.model_out}_repositories import {self.model_out_name}{self.model_in_name}sRepository",
            f"from {self.python_path_in}.managers.{self.model_in}_managers import {self.model_in_name}TableManager",
        )
        self._add_code(manager_path, class_name, code, import_statements)

    def add_repository(self):
        repository_path = os.path.join(
            self.path_out, "repositories", f"{self.model_out}_repositories.py"
        )
        class_name = f"{self.model_out_name}{self.model_in_name}sRepository"
        code = f"""class {class_name}({self.model_in_name}Repository):
    def receive(self, apply_filter=True):
        {self.model_out}_hub = {self.model_out_name}HubValueDate.objects.get(
            pk=self.session_data.get("pk")
        ).hub
        return super().receive(apply_filter).filter({self.model_out}_id={self.model_out}_hub.id)
                """
        import_statements = (
            f"from {self.python_path_in}.repositories.{self.model_in}_repositories import {self.model_in_name}Repository",
            f"from {self.python_path_out}.models.{self.model_out}_hub_models import {self.model_out_name}HubValueDate",
        )
        self._add_code(repository_path, class_name, code, import_statements)

    def add_urls(self):
        urls_path = os.path.join(self.path_out, "urls", f"{self.model_out}_urls.py")
        with open(urls_path, "r") as f:
            old_code = f.read()
        code = f"""path(
        "{self.model_out}/<int:pk>/{self.model_in}s/list",
        {self.model_out_name}{self.model_in_name}sListView.as_view(),
        name="{self.model_out}_{self.model_in}s_list"
    ),
    path(
        "{self.model_out}/<int:pk>/{self.model_in}/create",
        {self.model_out_name}{self.model_in_name}CreateView.as_view(),
        name="{self.model_out}_{self.model_in}_create"
    ),

    ]
    """
        new_code = old_code.replace("]", code)
        import_statements = (
            f"from {self.python_path_out}.views.{self.model_out}_views import {self.model_out_name}{self.model_in_name}sListView",
            f"from {self.python_path_out}.views.{self.model_out}_views import {self.model_out_name}{self.model_in_name}CreateView",
        )
        new_code = "\n".join(import_statements) + "\n" + new_code
        with open(urls_path, "w") as f:
            f.write(new_code)
