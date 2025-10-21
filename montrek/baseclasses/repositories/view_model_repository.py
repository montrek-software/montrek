from django.db import models


class ViewModelRepository:
    def __init__(self, view_model: None | type[models.Model]):
        self.view_model = view_model

    def has_view_model(self) -> bool:
        return self.view_model is not None
