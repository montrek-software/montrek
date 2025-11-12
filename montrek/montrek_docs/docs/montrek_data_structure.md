Montrek Data Structure

## Overview

The Montrek framework is built around a data structure that consists of several key components: Hubs, HubValueDates, Satellites, TimeSeriesSatellites, and Links. Understanding the relationships between these components is crucial for setting up a Montrek data model and using Django's migrations to make them work in the database.

## Hubs

Hubs are the central entities in the Montrek data structure. They represent the main objects or concepts that are being modeled. Hubs are defined as Django models that inherit from `MontrekHubABC`.

## HubValueDates

HubValueDates are used to track changes to Hubs over time. They represent a link between a hub and a certain point in time (value_date). HubValueDates are defined as Django models that inherit from `HubValueDate`.

## Satellites

Satellites are used to store data related to Hubs. They can be thought of as "attachments" to Hubs. Satellites are defined as Django models that inherit from `MontrekSatelliteABC`.

## TimeSeriesSatellites

TimeSeriesSatellites are a special type of Satellite that is used to store time-series data related to Hubs. They are defined as Django models that inherit from `MontrekSatelliteBaseABC`.

## Links

Links are used to establish relationships between two Hubs. There are several types of Links, including `MontrekOneToManyLinkABC`, `MontrekManyToManyLinkABC` and `MontrekOneToOneLinkABC`.

## Relationships

The relationships between these components are as follows:

- A Hub can have multiple HubValueDates.
- A HubValueDate is associated with one Hub and one value_date.
- A Satellite is associated with one Hub.
- A TimeSeriesSatellite is associated with one HubValueDate.
- A Link establishes a relationship between two Hubs.

## Example

Here is an example of how to set up a Montrek data model:

```python
from django.db import models
from baseclasses.models import MontrekHubABC, MontrekSatelliteABC, HubValueDate, MontrekTimeSeriesSatelliteABC, MontrekOneToManyLinkABC

class SideHub(MontrekHubABC):
  pass
class MyHub(MontrekHubABC):
  link_my_hub_side_hub = models.ManyToManyField(
    "SideHub", reated_name="link_side_hub_my_hub", through = "LinkMyHubSideHub"
  )

class MyHubValueDate(HubValueDate):
  hub = HubForeignKey(MyHub)


class MySatellite(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(MyHub, on_delete=models.CASCADE)
    data = models.TextField()
    number = models.IntegerField()

    identifier_fields = ["data"]

class MyTimeSeriesSatellite(MontrekTimeSeriesSatelliteABC):
    hub = models.ForeignKey(MyHub, on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=10, decimal_places=2)

class LinkMyHubSideHub(MontrekOneToManyLinkABC):
    hub_id = models.ForeignKey(MyHub, on_delete=models.CASCADE)
    hub_out = models.ForeignKey(SideHub, on_delete=models.CASCADE)
```

To use Django's migrations to make this data model work in the database, you would need to create migrations by doing `python manage.py makemigrations`

## Summary

In summary, the Montrek data structure consists of Hubs, HubValueDates, Satellites, TimeSeriesSatellites, and Links. Understanding the relationships between these components is crucial for setting up a Montrek data model and using Django's migrations to make them work in the database. By following the example above, you can create your own Montrek data model and use it to build data-driven applications.
