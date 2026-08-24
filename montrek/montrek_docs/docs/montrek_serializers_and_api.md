Montrek Serializers and API

## Overview

Montrek provides a set of serializers and API views to handle data serialization and deserialization. This section covers the serializer classes, API views, and endpoints.

## Serializer Classes

### MontrekSerializer

The `MontrekSerializer` class is the base serializer class in Montrek. It provides a standardized way to serialize and deserialize data.

```python
from rest_framework import serializers
from baseclasses.serializers import MontrekSerializer

class MyModelSerializer(MontrekSerializer):
    class Meta:
        model = MyModel
        fields = ['id', 'name', 'description']
```

## API Views and Endpoints

### MontrekApiViewMixin

The `MontrekApiViewMixin` class provides a set of methods to handle API requests. It can be used to create API views that handle GET, POST, PUT, and DELETE requests.

```python
from rest_framework.response import Response
from baseclasses.views import MontrekApiViewMixin

class MyApiView(MontrekApiViewMixin):
    def get(self, request):
        # Handle GET request
        pass

    def post(self, request):
        # Handle POST request
        pass

    def put(self, request):
        # Handle PUT request
        pass

    def delete(self, request):
        # Handle DELETE request
        pass
```

### API Endpoints

Montrek provides a set of API endpoints to handle data serialization and deserialization. The following table lists the available API endpoints:

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/data/` | GET | Retrieve a list of data objects |
| `/api/data/` | POST | Create a new data object |
| `/api/data/{id}/` | GET | Retrieve a single data object |
| `/api/data/{id}/` | PUT | Update a single data object |
| `/api/data/{id}/` | DELETE | Delete a single data object |

## Authentication

Every REST request is authenticated with a JWT bearer token, which a client
obtains from its Montrek user name (the e-mail address) and password:

| Endpoint | Method | Description |
| --- | --- | --- |
| `/rest_api/token/` | POST | Obtain an `access` and a `refresh` token |
| `/rest_api/token/refresh/` | POST | Exchange a refresh token for a new access token |
| `/rest_api/token/verify/` | POST | Check whether a token is still valid |

```bash
curl -X POST https://<host>/rest_api/token/ \
     -d "email=service@example.com" -d "password=<password>"
# {"access": "<access token>", "refresh": "<refresh token>"}
```

Access tokens are short lived (15 minutes) and refresh tokens rotate, so a
long-running service has to refresh rather than cache a token (see
`SIMPLE_JWT` in `settings.py`).

A view served by `MontrekApiViewMixin` answers as an API only when the request
carries `?gen_rest_api=true`; without it the very same URL keeps rendering HTML
for the browser. The mixin runs the Django permission check of the view on top
of the token check, so an API client needs exactly the permissions a user needs
for the same page.

## Uploading Files through the API

`MontrekUploadFileView` accepts a multipart POST from an outside service. It is
opt-in per view, because an upload endpoint writes data:

```python
class MontrekExampleA1UploadFileView(MontrekUploadFileView):
    file_upload_manager_class = A1FileUploadManager
    accept = ".csv"
    do_rest_upload = True
```

The client posts the file to the same URL the browser form posts to:

```bash
curl -X POST "https://<host>/montrek_example/a1_upload_file?gen_rest_api=true" \
     -H "Authorization: Bearer <access token>" \
     -F "file=@a_file.csv"
# 202 {"registry_id": 17, "celery_task_id": "...", "status": "pending",
#      "message": "Successfully scheduled background task for processing. ..."}
```

Any further form field of the view's `upload_form_class` is sent alongside the
file as an ordinary multipart field.

| Status | Meaning |
| --- | --- |
| `202` | Accepted; the pipeline runs on a Celery worker |
| `200` | Processed synchronously and succeeded (`do_process_file_async = False`) |
| `400` | The upload form is invalid, `errors` holds the form errors |
| `401` | Missing, expired or invalid token |
| `403` | The user lacks the permission the view requires |
| `415` | The file type is not in the view's `accept` list |
| `422` | Processed synchronously and failed |

Because processing is asynchronous, `202` means *accepted*, not *imported*. The
caller polls the outcome on the upload registry view of the same app, which is
a `MontrekListView` and therefore answers `gen_rest_api` requests out of the box:

```bash
curl "https://<host>/montrek_example/a1_view_uploads?gen_rest_api=true" \
     -H "Authorization: Bearer <access token>"
# [{"file_name": "a_file.csv", "upload_status": "processed", ...}]
```

`upload_status` runs `pending` -> `in_progress` -> `processed` or `failed`;
`upload_message` carries the reason when it failed.

## Data Serialization and Deserialization

Montrek provides a set of methods to handle data serialization and deserialization. The following table lists the available methods:

| Method | Description |
| --- | --- |
| `serialize_data` | Serialize a data object into a JSON string |
| `deserialize_data` | Deserialize a JSON string into a data object |

```python
from baseclasses.serializers import MontrekSerializer

data = {'id': 1, 'name': 'John Doe', 'description': 'This is a test'}
serializer = MontrekSerializer(data)
serialized_data = serializer.serialize_data()
print(serialized_data)  # Output: '{"id": 1, "name": "John Doe", "description": "This is a test"}'

deserialized_data = serializer.deserialize_data(serialized_data)
print(deserialized_data)  # Output: {'id': 1, 'name': 'John Doe', 'description': 'This is a test'}
```

## Summary

Montrek provides a set of serializers and API views to handle data serialization and deserialization. The `MontrekSerializer` class provides a standardized way to serialize and deserialize data, while the `MontrekApiViewMixin` class provides a set of methods to handle API requests. The API endpoints and methods provided by Montrek enable developers to easily handle data serialization and deserialization in their applications.
