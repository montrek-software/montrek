from dataclasses import dataclass
from baseclasses.views import MontrekTemplateView


@dataclass
class AuthenticatorViewMetaData:
    template_name: str


class AuthenticatorView(MontrekTemplateView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.meta_data = self._get_meta_data_instance()

    def _get_meta_data_instance(self):
        return AuthenticatorViewMetaData(template_name="wummsi")

    @property
    def template_name(self) -> str:
        return self.meta_data.template_name

    def get_template_context(self) -> dict:
        return {}
