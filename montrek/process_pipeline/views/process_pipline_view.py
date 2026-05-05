from baseclasses.views import MontrekRedirectView


class ProcessPipelineViewABC(MontrekRedirectView):
    success_url = "under_construction"

    def get_redirect_url(self, *args, **kwargs) -> str:
        self.process()
        return self.success_url

    def process(self):
        raise NotImplementedError("Implement process method")
