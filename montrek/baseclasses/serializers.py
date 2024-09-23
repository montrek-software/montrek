from rest_framework import serializers
from reporting.dataclasses import table_elements as te


class MontrekSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        self.manager = kwargs.pop("manager", None)
        super(MontrekSerializer, self).__init__(*args, **kwargs)
        if self.manager:
            table_elements = self.manager.table_elements
            self._setup_serializer(table_elements)

        else:
            raise NotImplementedError("Repository not provided to serializer")

    def _setup_serializer(self, table_elements):
        for element in table_elements:
            if isinstance(element, te.LinkTableElement):
                continue
            self.fields[element.attr] = element.serializer_field
