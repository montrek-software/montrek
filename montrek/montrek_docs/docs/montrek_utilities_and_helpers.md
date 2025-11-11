Montrek Utilities and Helpers

## Utility Functions

### `montrek_time`

The `montrek_time` function creates a timezone-aware datetime object.

```python
from baseclasses.utils import montrek_time

# Create a timezone-aware datetime object
dt = montrek_time(2022, 12, 25, 12, 0, 0)
print(dt)
```

### `get_content_type`

The `get_content_type` function returns the content type of a given object.

```python
from baseclasses.utils import get_content_type

# Get the content type of a given object
content_type = get_content_type(obj)
print(content_type)
```

## Helper Classes

### `TableMetaSessionData`

The `TableMetaSessionData` class provides a way to store and retrieve table metadata in the session.

```python
from baseclasses.utils import TableMetaSessionData

# Create a TableMetaSessionData object
table_meta = TableMetaSessionData(session)

# Set table metadata
table_meta.set_metadata('table_name', 'column_name')

# Get table metadata
metadata = table_meta.get_metadata('table_name')
print(metadata)
```

## Miscellaneous Functionality

### `HtmlSanitizer`

The `HtmlSanitizer` class provides a way to sanitize HTML input.

```python
from baseclasses.sanitizer import HtmlSanitizer

# Create an HtmlSanitizer object
sanitizer = HtmlSanitizer()

# Sanitize HTML input
sanitized_html = sanitizer.sanitize(html_input)
print(sanitized_html)
```

## Summary

The Montrek framework provides a set of utility functions and helper classes to aid in the development of data-driven applications. These utilities include timezone-aware datetime creation, content type retrieval, table metadata storage, and HTML sanitization.

## Next Steps

To learn more about the Montrek framework and its features, please refer to the official documentation and tutorials. Additionally, you can explore the Montrek example project to see how these utilities are used in practice.
