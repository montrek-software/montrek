from django.db.models import ForeignKey, CASCADE


class HubForeignKey(ForeignKey):
    def __init__(self, *args, **kwargs):
        on_delete = kwargs.pop("on_delete", CASCADE)
        related_name = kwargs.pop("related_name", "hub_value_date")
        super().__init__(
            *args, on_delete=on_delete, related_name=related_name, **kwargs
        )
