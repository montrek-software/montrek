import datetime
from copy import deepcopy
from typing import Any

from baseclasses.models import MontrekHubABC
from django.db import models


class ViewModelRepository:
    def __init__(self, view_model: None | type[models.Model]):
        self.view_model = view_model

    def has_view_model(self) -> bool:
        return self.view_model is not None

    @classmethod
    def generate_view_model(
        cls,
        module_name: str,
        repository_name: str,
        hub_class: type[MontrekHubABC],
        fields: dict[str, Any],
    ) -> type[models.Model]:
        class Meta:
            # Only works if repository is in repositories folder
            app_label = module_name.split(".repositories")[0].split(".")[-1]
            managed = True
            db_table = f"{app_label}_{repository_name.lower()}_view_model"

        for key, field in fields.items():
            field = deepcopy(field)
            field.null = True
            field.blank = True
            field.name = key
            fields[key] = field

        fields["value_date_list_id"] = models.IntegerField(null=True, blank=True)
        fields["hub"] = models.ForeignKey(hub_class, on_delete=models.CASCADE)

        attrs = {
            "__module__": repository_name,
            "Meta": Meta,
            "reference_date": datetime.date.today(),
        }
        attrs.update(fields)
        model_name = repository_name + "ViewModel"
        model = type(model_name, (models.Model,), attrs)
        return model
