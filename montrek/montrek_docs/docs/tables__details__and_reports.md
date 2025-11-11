Tables, Details, and Reports

## Definition

In Montrek, tables, details, and reports are essential components for displaying and managing data. Tables provide a structured way to present data, while details offer a more in-depth view of specific data points. Reports, on the other hand, allow users to generate summaries and analysis of their data.

## Rendering

### Tables

Tables in Montrek are rendered using the `MontrekTableManagerABC` class. This class provides a basic structure for creating tables and can be extended to accommodate specific use cases.

```python
class MontrekTableManagerABC(MontrekManager, metaclass=MontrekTableMetaClass):
    table_title = ""
    document_title = "Montrek Table"
    draft = False
    is_compact_format = False
    is_large: bool = False

    def __init__(self, session_data: SessionDataType = {}):
        super().__init__(session_data)
        self._document_name: None | str = None
        self._queryset: None | QuerySet = None
        self.is_current_compact_format: bool = self.get_is_compact_format()
        self.order_field: None | str = self.get_order_field()
```

### Details

Details in Montrek are rendered using the `MontrekDetailsManager` class. This class provides a basic structure for creating details pages and can be extended to accommodate specific use cases.

```python
class MontrekDetailsManager(MontrekManager):
    table_cols = 2
    table_title = ""
    document_title = "Montrek Details"
    document_name = "details"
    draft = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.object_query = self.get_object_from_pk(
            self.session_data.get("pk", "Unknown")
        )
        self.row_size = math.ceil(len(self.table_elements) / self.table_cols)
```

### Reports

Reports in Montrek are rendered using the `MontrekReportManager` class. This class provides a basic structure for creating reports and can be extended to accommodate specific use cases.

```python
class MontrekReportManager(MontrekManager):
    document_name = "document"
    document_title = "Montrek Report"
    send_mail_url = "send_mail"
    draft = False

    def __init__(self, session_data: dict[str, str], **kwargs) -> None:
        super().__init__(session_data=session_data, **kwargs)
        self._report_elements = []
```

## Connection to Models or Views

Tables, details, and reports in Montrek can be connected to models or views using the `MontrekManager` class. This class provides a basic structure for interacting with models and views and can be extended to accommodate specific use cases.

```python
class MontrekManager:
    repository_class = MontrekRepository
    _repository = None

    def __init__(self, session_data: dict[str, Any] | None = None):
        if session_data is None:
            session_data = {}
        self.session_data = session_data
        self.messages: list[MontrekMessage] = []

    @property
    def repository(self):
        if self._repository is None:
            self._repository = self.repository_class(self.session_data)
        return self._repository

    def create_object(self, **kwargs) -> Any:
        return self.repository.create_by_dict(**kwargs)

    def delete_object(self, pk: int):
        object_query = self.get_object_from_pk(pk)
        return self.repository.delete(object_query.hub)

    def get_object_from_pk(self, pk: int):
        return self.repository.get_object_from_pk(pk)
```

## Summary

In summary, tables, details, and reports are essential components of Montrek that provide a structured way to present and manage data. The `MontrekTableManagerABC`, `MontrekDetailsManager`, and `MontrekReportManager` classes provide a basic structure for creating tables, details, and reports, respectively. These classes can be extended to accommodate specific use cases and can be connected to models or views using the `MontrekManager` class.

## Next Steps

To get started with using tables, details, and reports in Montrek, follow these next steps:

1. Import the necessary classes and modules.
2. Create a new instance of the `MontrekTableManagerABC`, `MontrekDetailsManager`, or `MontrekReportManager` class.
3. Define the table title, document title, and other attributes as needed.
4. Use the `create_object`, `delete_object`, and `get_object_from_pk` methods to interact with models and views.
5. Extend the `MontrekManager` class to accommodate specific use cases.

By following these steps, you can effectively use tables, details, and reports in Montrek to manage and present your data.
