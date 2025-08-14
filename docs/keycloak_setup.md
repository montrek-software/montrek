# Keycloak Setup Guide

This guide explains how to bring up Keycloak with Docker Compose, configure TLS, enable 2‑factor authentication (2FA), and connect your application. It also includes how to add users. The instructions assume you are using the bootstrap/init approach that imports a realm at startup (with OTP and password set as default **Required Actions**).

---

## Prerequisites

- Docker & Docker Compose
- DNS (or `/etc/hosts`) entries so that:
  - `auth.$PROJECT_NAME.$DEPLOY_HOST` resolves to your Keycloak reverse proxy
  - `$PROJECT_NAME.$DEPLOY_HOST` resolves to your app’s reverse proxy

> **Note:** The realm import runs only on first boot (i.e., when the realm does **not** yet exist in the DB). Subsequent restarts reuse what’s already stored in Postgres.

---

## 1) Stop any running containers

```bash
make docker-down
```

---

## 2) Configure `.env`

Add or update the required variables. Example:

```dotenv
# Enable Keycloak services in compose
ENABLE_KEYCLOAK=1

# Database
KEYCLOAK_DB_PASSWORD=keycloak

# Keycloak service
KEYCLOAK_PORT=8080
KEYCLOAK_REALM=montrek_realm
KEYCLOAK_CLIENT_ID=montrek_client
KEYCLOAK_CLIENT_SECRET=        # leave empty for public + PKCE;
KEYCLOAK_ADMIN=admin
ADMIN_PASSWORD=supersecret     # passed as KEYCLOAK_ADMIN_PASSWORD

# Routing / hostnames
PROJECT_NAME=test
DEPLOY_HOST=montrek-local.lan
```

---

## 3) TLS certificates

- **Local/trusted server** (you control the trust chain):

  ```bash
  make server-generate-https-certs
  ```

  This regenerates local certs for the reverse proxy.

- **Public server** (public CA):
  Ensure your certificate (e.g., `fullchain.crt`) **covers**:

  ```
  auth.$PROJECT_NAME.$DEPLOY_HOST
  ```

  (and any additional hostnames you serve, e.g., `$PROJECT_NAME.$DEPLOY_HOST`).

---

## 4) Rebuild the reverse proxy (nginx)

```bash
make docker-build
```

---

## 5) Start the stack

```bash
make docker-up
```

On startup the Keycloak container:

- Generates the realm import JSON from your environment variables.
- Starts Keycloak with `--import-realm` (import happens only if the realm is not yet present).

---

## 6) Log in to the Keycloak Admin Console

Open:

```
https://auth.$PROJECT_NAME.$DEPLOY_HOST
```

Sign in with:

- **Username:** `admin` (or `$KEYCLOAK_ADMIN` if customized)
- **Password:** `$ADMIN_PASSWORD`

---

## 7) Select your realm

Use the realm dropdown (top-left) to select:

```
$KEYCLOAK_REALM
```

---

## 8) Enable 2FA in the Browser flow

To enforce OTP at login:

1. Go to **Authentication → Flows**.
2. Select the **browser** flow.
3. Set **“Browser – Conditional OTP”** to **Required**.

> The realm import already sets **Configure OTP** as a default _Required Action_, which makes new users enroll an authenticator on first login. Setting the Browser flow’s _Conditional OTP_ to **Required** ensures OTP is enforced during login for users who have OTP configured.

---

## 9) Switch the client to **confidential** and capture the secret

1. Go to **Clients → `$KEYCLOAK_CLIENT_ID`**.
2. In **Capability config** (or **Access type** on older UIs), enable **Client authentication** (i.e., make it confidential).
3. Go to the **Credentials** tab and copy the **Secret**.
4. Update your `.env`:

   ```dotenv
   KEYCLOAK_CLIENT_SECRET=<copied-secret>
   ```

5. Restart the app with `make docker-restart`

---

## 10) Test application login

Visit your app:

```
https://$PROJECT_NAME.$DEPLOY_HOST
```

You should be redirected to the Keycloak login screen for your realm. Log in with the `$ADMIN_EMAIL`.

---

# How to add a new user

1. In your realm, go to **Users → Add user**.
2. Fill in the user’s details (username, email, names).
3. In **Required actions**, add **Update Password** (and keep **Configure OTP** if you want them to enroll an authenticator at first login).
4. Save the user.
5. Go to the **Credentials** tab and set a **temporary password** (mark it **Temporary**).
6. Share the username and temporary password with the user. On first login they must change their password and complete any required actions (e.g., OTP enrollment).

---

## Troubleshooting

- **No password/OTP prompt after enabling required actions:**
  The user likely has an existing SSO session. Log them out via **Users → Sessions → Logout**, or trigger logout from the app, or force re-auth with an authorization request parameter like `prompt=login`.

- **Redirect URI errors:**
  Ensure the client’s **Redirect URIs** include `https://$PROJECT_NAME.$DEPLOY_HOST/*` (this is written by the init script).

- **Public client with secret set:**
  Public clients ignore secrets. If you set a secret in `.env`, also switch the client to **confidential** in Keycloak.

- **Certificates not trusted (local):**
  For local development, install/trust the generated CA/certificates on your machine. For public deployments, ensure the CA‑issued certificate covers **auth.$PROJECT_NAME.$DEPLOY_HOST** (and any other hostnames).

---

## Notes on this setup

- The realm import runs only on first boot. Changes to flows (e.g., setting Browser – Conditional OTP to **Required**) are usually done via the Admin UI or scripted using `kcadm.sh` after startup.
