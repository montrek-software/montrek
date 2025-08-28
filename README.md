# montrek

**montrek** is a flexible software platform for data management, report generation, data analysis, and providing a web interface for easy interaction.
It is highly customizable and can be adapted for a wide range of applications.

---

## Installation Guide

### Prerequisites

Before installing, ensure the following are available on your system:

- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [GitHub access via SSH](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account)
- OpenSSL
- `make`
- [Docker](https://docs.docker.com/engine/install/)
- Docker must be accessible for your user (ensure your user is in the `docker` group)

---

### Clone the Repository

Run:

```bash
git clone git@github.com:chrishombach/montrek.git <your-folder>
```

---

### Configure Environment

The `.env` file is the **central configuration file** for montrek.
It contains sensitive information and should be handled carefully.

1. Copy the template:

   ```bash
   cp .env.template .env
   ```

2. Fill in all required configuration values inside `.env`.

---

### Generate HTTPS Certificates

From the project root directory, run:

```bash
make server-generate-https-certs
```

Follow the prompts to provide certificate details.

---

### Add Additional Repositories

If your project requires additional client or montrek repositories:

1. Clone the repository inside the **montrek base folder**:

   ```bash
   make clone-repository <name_of_repo>
   ```

2. Register the repository in `.env` by updating `NAVBAR_APPS`.

   Example:

   ```bash
   make clone-repository mt_economic_common
   ```

   Then set in `.env`:

   ```
   NAVBAR_APPS=mt_economic_common.country,mt_economic_common.currency
   ```

---

### Start Docker

Build and start the containers:

```bash
make docker-up
```

Once running, you can access montrek in your browser at:

```
https://<PROJECT_NAME>.<DEPLOY_HOST>
```

---

### Keycloak Setup (Optional)

By default, montrek uses Django’s authentication framework.
If you need **two-factor authentication** or advanced user management, enable **Keycloak**.

Instructions are available in:
`docs/keycloak_setup.md`

---

## Local Setup (For Developers)

For development, the Django application can be run locally without Docker.

### 1. Setup Python Environment

Initialize a local environment:

```bash
make local-init
```

This sets up a `pyenv` virtual environment and installs all dependencies.

---

### 2. Setup Database

The easiest option is to use the database running inside Docker.

1. In `.env`, set:

   ```
   DB_HOST=localhost
   ```

2. Start the database container:

   ```bash
   docker compose up db -d
   ```

---

### 3. Run Application

For debugging and local development:

1. Enable debug mode in `.env`:

   ```
   DEBUG=1
   ```

2. Start the Django server:

   ```bash
   cd montrek
   python manage.py runserver
   ```

3. Open the application in your browser.

4. If running for the first time (or after new migrations):

   ```bash
   python manage.py migrate
   ```

---

## Common Tasks

### Update Requirements

To add new dependencies:

1. Add packages to the relevant `requirements.in` file (base or module-specific).
2. Sync and install dependencies:

   ```bash
   make sync-local-python-env
   ```

---

### Database Backup

Create a backup:

```bash
make docker-db-backup
```

- Ensure `db` and `web` containers are running.
- Backup files are stored in `db_backups/`.
- Old backups are pruned automatically:
  - Older than **30 days** (unless end-of-month) → deleted.
  - Older than **1 year** → deleted.

To automate backups on Unix systems, add a cronjob:

```bash
crontab -e
```

Example entry (daily at 10:15):

```
15 10 * * * cd <path-to-montrek> && make docker-db-backup
```

---

### Database Restore

To restore a backup:

```bash
make docker-db-restore
```

You will be prompted to enter the backup date you want to restore.
