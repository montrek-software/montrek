# montrek REST API

The REST API is not a separate set of URLs. Most montrek pages also answer as
JSON: call the page's normal URL with `?gen_rest_api=true` and an
`Authorization: Bearer <token>` header.

```
GET /montrek_example/a/list?gen_rest_api=true
Authorization: Bearer <access token>
```

The API applies the same permissions as the browser. A user who cannot open a
page cannot read it through the API either.

## 1. Get an access token

Which way to use depends on how users log in to the instance.

### a) Django login (no Keycloak)

Post email and password to `/rest_api/token/`:

```python
resp = requests.post(
    f"{SERVER}/rest_api/token/",
    json={"email": "user@example.com", "password": "..."},
    timeout=10,
)
tokens = resp.json()
access = tokens["access"]    # valid for 15 minutes
refresh = tokens["refresh"]  # valid for 7 days
```

| Endpoint                  | Body                  | Returns                         |
| ------------------------- | --------------------- | ------------------------------- |
| `/rest_api/token/`        | `{email, password}`   | `{access, refresh}`             |
| `/rest_api/token/refresh/`| `{refresh}`           | `{access, refresh}` (rotated)   |
| `/rest_api/token/verify/` | `{token}`             | `200` if valid, `401` otherwise |

### b) Keycloak login (`ENABLE_KEYCLOAK=true`)

Users who log in through Keycloak have **no Django password**, so
`/rest_api/token/` answers `No active account found with the given
credentials`. Get the token from Keycloak instead:

```python
REALM_URL = "https://auth-<PROJECT_NAME>.<DEPLOY_HOST>/realms/<REALM>"

resp = requests.post(
    f"{REALM_URL}/protocol/openid-connect/token",
    data={  # form-encoded, not JSON
        "grant_type": "password",
        "client_id": "<client-id>",
        "client_secret": "<client-secret>",  # only for confidential clients
        "username": "user@example.com",
        "password": "...",
    },
    timeout=10,
)
access = resp.json()["access_token"]
```

Requirements in Keycloak:

- The client needs **"Direct access grants"** enabled for the password grant.
  Use a client for API scripts rather than the web app's client.
- For automated jobs without a person, use `grant_type=client_credentials` on a
  client with a service account.
- Refresh with `grant_type=refresh_token` against the same endpoint.

montrek checks Keycloak tokens against Keycloak's userinfo endpoint and maps
them to the Django user with the same email, as the browser login does
(`rest_api/authentication.py`). montrek's own tokens keep working alongside.

## 2. Call the API

```python
resp = requests.get(
    f"{SERVER}/montrek_example/a/list",
    params={"gen_rest_api": "true"},
    headers={"Authorization": f"Bearer {access}"},
    timeout=100,
)
data = resp.json()
```

What answers to `gen_rest_api=true`:

| View type                               | Response                                   |
| --------------------------------------- | ------------------------------------------ |
| List views (`MontrekListView`)          | JSON list, one object per table row        |
| Detail views (`MontrekDetailView`)      | JSON object of the entity                  |
| Report views (`MontrekReportView`)      | The report's data as JSON                  |
| `MontrekRestApiView`                    | Always JSON, no query parameter needed     |
| Upload views with `do_rest_upload=True` | `POST` multipart file upload, see below    |

### File uploads

Upload views that set `do_rest_upload = True` accept a multipart `POST`:

```python
with open("data.csv", "rb") as file:
    resp = requests.post(
        f"{SERVER}/montrek_example/a1_upload_file",
        params={"gen_rest_api": "true"},
        headers={"Authorization": f"Bearer {access}"},
        files={"file": file},
        timeout=100,
    )
```

The response contains `registry_id`, `celery_task_id`, `status` and
`message`. Status codes:

- `202` – accepted, processing runs asynchronously. Poll the upload registry
  list view (here `/montrek_example/a1_view_uploads?gen_rest_api=true`) for
  the outcome.
- `200` – processed synchronously and succeeded.
- `422` – processed synchronously and failed.
- `400` – invalid request (e.g. missing file or wrong file type).

## Errors

| Status | Meaning                                                            |
| ------ | ------------------------------------------------------------------ |
| `401`  | No token, or the token is invalid or expired – get a new one       |
| `403`  | Authenticated, but the user lacks the permission for this view     |

## Making a view available in the API

- List, detail and report views get it for free from `MontrekApiViewMixin`.
- For a JSON-only endpoint, subclass `MontrekRestApiView` and set
  `permission_required`. Without it, any valid token can read the endpoint.
- Upload views opt in with `do_rest_upload = True`, because they write data.
