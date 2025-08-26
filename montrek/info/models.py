from baseclasses.models import MontrekHubABC


class TestHubA(MontrekHubABC):
    class Meta:
        app_label = "info"
        managed = False


class TestHubB(MontrekHubABC):
    class Meta:
        app_label = "info"
        managed = False
