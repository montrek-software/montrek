Montrek Utilities and Helpers

## Overview

The Montrek framework provides a set of utility functions and helper classes to facilitate the development of data-driven applications. These utilities and helpers are designed to simplify common tasks and provide a consistent interface for interacting with the framework.

## Utility Functions

### `montrek_time`

The `montrek_time` function creates a timezone-aware datetime object from a set of date and time components.

```python
from baseclasses.utils import montrek_time

dt = montrek_time(2022, 12, 25, 12, 0, 0)
print(dt)  # Output: 2022-12-25 12:00:00+00:00
```

### `get_content_type`

The `get_content_type` function returns the content type of a given object.

```python
from baseclasses.utils import get_content_type

obj = MyModel.objects.get(id=1)
content_type = get_content_type(obj)
print(content_type)  # Output: myapp.mymodel
```

## Helper Classes

### `TableMetaSessionData`

The `TableMetaSessionData` class provides a way to store and retrieve table metadata in the session.

```python
from baseclasses.utils import TableMetaSessionData

table_meta = TableMetaSessionData(request.session)
table_meta.set('my_table', {'columns': ['column1', 'column2']})
print(table_meta.get('my_table'))  # Output: {'columns': ['column1', 'column2']}
```

## Miscellaneous Functionality

### `HtmlSanitizer`

The `HtmlSanitizer` class provides a way to sanitize HTML input to prevent XSS attacks.

```python
from baseclasses.sanitizer import HtmlSanitizer

sanitizer = HtmlSanitizer()
html = '<script>alert("XSS")</script>'
sanitized_html = sanitizer.sanitize(html)
print(sanitized_html)  # Output: &lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;
```

## Summary

The Montrek framework provides a set of utility functions and helper classes to simplify common tasks and provide a consistent interface for interacting with the framework. These utilities and helpers can be used to perform tasks such as creating timezone-aware datetime objects, retrieving content types, storing and retrieving table metadata, and sanitizing HTML input.
