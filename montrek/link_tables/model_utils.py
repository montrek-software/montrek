from django.apps import apps

from baseclasses import models as baseclass_models

def new_link_entry(from_hub:baseclass_models.MontrekHubABC,
                   to_hub:baseclass_models.MontrekHubABC,
                   link_table:baseclass_models.MontrekLinkABC) -> None:
    link_table.objects.create(
        from_hub=from_hub,
        to_hub=to_hub)
