import factory
from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekSatelliteFactory,
)

from sftp.tests.factories.sftp_connection_hub_factories import SftpConnectionHubFactory
from sftp.models.sftp_connection_sat_models import SftpConnectionSatellite


class SftpConnectionSatelliteFactory(MontrekSatelliteFactory):
    class Meta:
        model = SftpConnectionSatellite

    hub_entity = factory.SubFactory(SftpConnectionHubFactory)
