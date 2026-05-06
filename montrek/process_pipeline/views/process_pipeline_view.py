from django.urls import reverse
from baseclasses.views import MontrekRedirectView


class ProcessPipelineViewABC(MontrekRedirectView):
    success_url = "under_construction"

    def get_success_url(self) -> str:
        return reverse(self.success_url)

    def get_redirect_url(self, *args, **kwargs) -> str:
        self.process()
        self.show_messages()
        return self.get_success_url()

    def process(self):
        raise NotImplementedError("Implement process method")
