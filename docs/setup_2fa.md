# Keycloak Integration Guide

This guide explains how to enable **Keycloak** in the local development setup for authentication and 2FA support in your Django application.

## Environment Configuration

To enable Keycloak, add the following environment variables to your `.env` file:

**Required `.env` entries:**

ENABLE_KEYCLOAK=1  
KEYCLOAK_PORT=8080  
KEYCLOAK_DB_PORT=5432  
KEYCLOAK_DB_PASSWORD=keycloak  
KEYCLOAK_ADMIN_PASSWORD=admin

### Variable Descriptions

| Variable                | Description                        |
| ----------------------- | ---------------------------------- |
| ENABLE_KEYCLOAK         | Set to `1` to enable Keycloak      |
| KEYCLOAK_PORT           | Port to expose Keycloak externally |
| KEYCLOAK_DB_PASSWORD    | Password for the Keycloak database |
| KEYCLOAK_ADMIN_PASSWORD | Admin account password in Keycloak |

---

## Starting Keycloak

Once the `.env` file is configured, start the services with:

**Command:**

make docker-up

This command will:

- Start your application services
- Launch Keycloak (if `ENABLE_KEYCLOAK=1`)
- Start the associated Keycloak PostgreSQL database

---

## Accessing Keycloak

After startup, you can access the Keycloak admin console at:

http://<your-ip>:<KEYCLOAK_PORT>

**Example (default configuration):**

http://localhost:8080

---

## Default Login Credentials

Use the following credentials to log in to Keycloak:

- **Username:** admin
- **Password:** Value of `KEYCLOAK_ADMIN_PASSWORD` (default: `admin`)

---

## Notes

- Make sure `ENABLE_KEYCLOAK=1` is set in `.env` before running `make docker-up`, otherwise the Keycloak service will not be started.
- You can change `KEYCLOAK_PORT` and `KEYCLOAK_DB_PORT` if these ports are already in use on your system.
- **Important:** Use secure passwords in production environments. The example values are for development only.

---

## Stopping Services

To stop all services, run:

make docker-down

This will gracefully shut down the containers.

---

## Troubleshooting

- If you cannot access Keycloak, ensure the port specified in `KEYCLOAK_PORT` is not blocked or used by another service.
- If you change `.env` after the services are running, restart the containers with:

make docker-down  
make docker-up
