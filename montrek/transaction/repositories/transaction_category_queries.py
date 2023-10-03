from django.apps import apps
from django.db.models import Q
from typing import Dict
import hashlib
from baseclasses import models as baseclass_models
from baseclasses.repositories.db_helper import new_satellite_entry
from baseclasses.repositories.db_helper import new_link_entry
from baseclasses.repositories.db_helper import select_satellite

def transaction_category_satellite():
    return apps.get_model("transaction", "TransactionCategorySatellite")


def transaction_category_map_satellite():
    return apps.get_model("transaction", "TransactionCategoryMapSatellite")

def transaction_satellite():
    return apps.get_model("transaction", "TransactionSatellite")

def set_transaction_category_by_value(
    transaction_satellite_object: baseclass_models.MontrekSatelliteABC, value: str
) -> None:
    transaction_category_hub = get_hubs_by_satellite_attribute(
        transaction_category_satellite(), "typename", value
    )[0]
    new_link_entry(
        from_hub=transaction_satellite_object.hub_entity,
        to_hub=transaction_category_hub,
        link_table=transaction_transaction_type_link(),
    )




def get_transaction_category_by_transaction(
    transaction_satellite_object: baseclass_models.MontrekSatelliteABC,
) -> str:
    transaction_hub = transaction_satellite_object.hub_entity
    transaction_category_hub = transaction_hub.link_transaction_transaction_category.all()
    if len(transaction_category_hub) == 0:
        transaction_category_hub = set_transaction_category_by_map(
            transaction_satellite_object
        )
    elif len(transaction_category_hub) == 1:
        transaction_category_hub = transaction_category_hub[0]
    else:
        raise Exception(
            "Transaction {} has multiple categories".format(transaction_hub.typename)
        )
    return select_satellite(
        hub_entity=transaction_category_hub,
        satellite_class=transaction_category_satellite(),
    )


def set_transaction_category_by_map(
    transaction_satellite_object: baseclass_models.MontrekSatelliteABC,
) -> baseclass_models.MontrekSatelliteABC:
    cat_typename = "UNKNOWN"
    for field in transaction_satellite_object.__class__().identifier_fields:
        field_value = getattr(transaction_satellite_object, field)
        if field_value is None:
            continue
        field_value = field+str(field_value).replace(' ','').upper()
        field_value_hash = hashlib.sha256(field_value.encode()).hexdigest()
        transaction_category_maps = transaction_category_map_satellite().objects.filter(
            Q(hash_searchfield=field_value_hash) &
            Q(hub_entity__is_deleted=False)
        )
        if len(transaction_category_maps) > 0:
            transaction_category_map_hub = transaction_category_maps[0].hub_entity
            transaction_category = select_satellite(
                transaction_category_map_hub,
                transaction_category_map_satellite(),
            )
            cat_typename = transaction_category.category.replace(' ','').upper()
            break

    transaction_category_sat = _set_transaction_category_to_transaction(
        transaction_satellite_object, cat_typename
    )
    return transaction_category_sat.hub_entity

def set_transaction_category_by_map_entry(
    transaction_category_map_entry: baseclass_models.MontrekSatelliteABC,
) -> None:
    account_hub = transaction_category_map_entry.hub_entity.link_transaction_category_map_account.first()
    transaction_satellites = transaction_satellite().objects.filter( 
        Q(hub_entity__link_transaction_account=account_hub) & 
        Q(hub_entity__is_deleted=False) 
    )
    if transaction_category_map_entry.is_regex:
        transaction_satellites = transaction_satellites.filter(
            Q(**{transaction_category_map_entry.field+'__regex': transaction_category_map_entry.value})
        )
    else:
        transaction_satellites = transaction_satellites.filter(
            Q(**{transaction_category_map_entry.field: transaction_category_map_entry.value})
        )

    for transaction_satellite_object in transaction_satellites:
        _set_transaction_category_to_transaction(
            transaction_satellite_object, transaction_category_map_entry.category
        )


def _set_transaction_category_to_transaction(
    transaction_satellite_object: baseclass_models.MontrekSatelliteABC,
    cat_typename: str,
) -> baseclass_models.MontrekSatelliteABC:
    cat_typename = cat_typename.replace(' ','').upper()
    transaction_category_sat = new_satellite_entry(
        satellite_class=transaction_category_satellite(),
        typename=cat_typename,
    )
    new_link_entry(
        from_hub=transaction_satellite_object.hub_entity,
        to_hub=transaction_category_sat.hub_entity,
        related_field="link_transaction_transaction_category",
    )

def add_transaction_category_map_entry(
    account_hub: baseclass_models.MontrekHubABC,
    data_entries: Dict
) -> baseclass_models.MontrekSatelliteABC:
    transaction_category_map = new_satellite_entry(
        transaction_category_map_satellite(),
        **data_entries,
    )
    account_hub.link_account_transaction_category_map.add(transaction_category_map.hub_entity)
    return transaction_category_map
