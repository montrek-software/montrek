from django.db import models
from rest_framework import serializers


class MontrekSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        self.repository = kwargs.pop("repository", None)
        super(MontrekSerializer, self).__init__(*args, **kwargs)
        if self.repository:
            fields = self.repository.std_satellite_fields()
            self._setup_serializer(fields)

        else:
            raise NotImplementedError("Repository not provided to serializer")

    def _setup_serializer(self, fields):
        for field in fields:
            if isinstance(field, models.CharField):
                self.fields[field.name] = serializers.CharField()
            elif isinstance(field, models.IntegerField):
                self.fields[field.name] = serializers.IntegerField()
            elif isinstance(field, models.FloatField):
                self.fields[field.name] = serializers.FloatField()
            elif isinstance(field, models.DateTimeField):
                self.fields[field.name] = serializers.DateTimeField()
            elif isinstance(field, models.DateField):
                self.fields[field.name] = serializers.DateField()
            elif isinstance(field, models.BooleanField):
                self.fields[field.name] = serializers.BooleanField()
            elif isinstance(field, models.TextField):
                self.fields[field.name] = serializers.CharField()
            else:
                raise NotImplementedError(f"Field type {field} not known to Serializer")
