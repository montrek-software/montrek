from rest_framework import serializers


class MontrekSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        self.repository = kwargs.pop("repository", None)
        if self.repository:
            self._meta.model = self.repository.hub_class
            self._meta.fields = self.repository.get_all_fields()
        else:
            raise NotImplementedError("Repository not provided to serializer")
        super(MontrekSerializer, self).__init__(*args, **kwargs)
