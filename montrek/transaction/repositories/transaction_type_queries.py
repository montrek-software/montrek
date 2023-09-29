from baseclasses import models as baseclass_models
from baseclasses.repositories.db_helper import get_hubs_by_satellite_attribute
from baseclasses.repositories.db_helper import new_link_entry
from baseclasses.repositories.db_helper import select_satellite
from django.apps import apps

def transaction_type_satellite():
    return apps.get_model("transaction", "TransactionTypeSatellite")

def get_transaction_type_by_transaction(
    transaction_satellite_object: baseclass_models.MontrekSatelliteABC,
) -> str:
    transaction_hub = transaction_satellite_object.hub_entity
    transaction_type_hub = transaction_hub.link_transaction_transaction_type.all()
    if len(transaction_type_hub) == 0:
        transaction_type_hub = _set_transaction_type_by_value(
            transaction_satellite_object
        )
    else:
        transaction_type_hub = transaction_type_hub[0]
    return select_satellite(
        hub_entity=transaction_type_hub, satellite_class=transaction_type_satellite()
    )


def set_transaction_type(
    transaction_satellite_object: baseclass_models.MontrekSatelliteABC,
    value: str = None,
) -> None:
    if value is None:
        _set_transaction_type_by_value(transaction_satellite_object)
    else:
        transaction_type_hub = get_hubs_by_satellite_attribute(
            transaction_type_satellite(), "typename", value
        )[0]
        new_link_entry(
            from_hub=transaction_satellite_object.hub_entity,
            to_hub=transaction_type_hub,
            related_field='link_transaction_transaction_type'
        )


def _set_transaction_type_by_value(
    transaction_satellite_object: baseclass_models.MontrekSatelliteABC,
) -> baseclass_models.MontrekHubABC:
    transaction_value = transaction_satellite_object.transaction_value
    if transaction_value >= 0:
        transaction_type_hub = get_hubs_by_satellite_attribute(
            transaction_type_satellite(), "typename", "INCOME"
        )[0]
    else:
        transaction_type_hub = get_hubs_by_satellite_attribute(
            transaction_type_satellite(), "typename", "EXPANSE"
        )[0]
    new_link_entry(
        from_hub=transaction_satellite_object.hub_entity,
        to_hub=transaction_type_hub,
        related_field='link_transaction_transaction_type'
    )
    return transaction_type_hub
