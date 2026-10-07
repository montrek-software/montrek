import factory

from baseclasses.tests.factories.baseclass_factories import ValueDateListFactory
from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekHubValueDateFactory,
    MontrekHubFactory,
)
from sftp.models.sftp_connection_hub_models import SftpConnectionHub
from sftp.models.sftp_connection_hub_models import SftpConnectionHubValueDate


class SftpConnectionHubFactory(MontrekHubFactory):
    class Meta:
        model = SftpConnectionHub


class SftpConnectionHubValueDateFactory(MontrekHubValueDateFactory):
    class Meta:
        model = SftpConnectionHubValueDate

    hub = factory.SubFactory(SftpConnectionHubFactory)
    value_date_list = factory.SubFactory(ValueDateListFactory)
