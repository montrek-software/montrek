Montrek Fields and Models

## Custom Fields

Montrek provides several custom fields that can be used in models. These fields are designed to work seamlessly with the Montrek framework and provide additional functionality.

### HubForeignKey

The `HubForeignKey` field is a custom foreign key field that links a satellite model to a hub model. It is used to establish relationships between models in the Montrek framework.

```python
from baseclasses.models import MontrekHubABC, MontrekSatelliteABC
from django.db import models

class MyHub(MontrekHubABC):
    pass

class MySatellite(MontrekSatelliteABC):
    hub = models.ForeignKey(MyHub, on_delete=models.CASCADE, related_name='satellites')
```

## Model Classes

Montrek provides several abstract base classes (ABCs) that can be used to create models. These ABCs provide a basic structure for models and include common fields and methods.

### MontrekHubABC

The `MontrekHubABC` class is an abstract base class that provides a basic structure for hub models. It includes fields for the hub's entity ID, value date, and created at timestamp.

```python
from baseclasses.models import MontrekHubABC
from django.db import models

class MyHub(MontrekHubABC):
    pass
```

### MontrekSatelliteABC

The `MontrekSatelliteABC` class is an abstract base class that provides a basic structure for satellite models. It includes fields for the satellite's entity ID, value date, and created at timestamp.

```python
from baseclasses.models import MontrekSatelliteABC
from django.db import models

class MySatellite(MontrekSatelliteABC):
    pass
```

## Inheritance Structure

The Montrek framework uses a hierarchical inheritance structure to organize models. Hub models inherit from `MontrekHubABC`, while satellite models inherit from `MontrekSatelliteABC`.

```python
from baseclasses.models import MontrekHubABC, MontrekSatelliteABC
from django.db import models

class MyHub(MontrekHubABC):
    pass

class MySatellite(MontrekSatelliteABC):
    hub = models.ForeignKey(MyHub, on_delete=models.CASCADE, related_name='satellites')
```

## Summary

In this section, we covered the custom fields and model classes provided by the Montrek framework. We also discussed the inheritance structure used by the framework to organize models.

## Next Steps

In the next section, we will cover the views and templates used in the Montrek framework. We will discuss how to create views and templates that work with the Montrek models and custom fields.
