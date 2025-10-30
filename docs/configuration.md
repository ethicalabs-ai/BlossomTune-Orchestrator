# Configuration

The application is configured primarily through environment variables, which are documented in `blossomtune_gradio/config.py` and set in your `docker-compose.yaml` or `.env` file.

## Key Environment Variables

* `BLOSSOMTUNE_CONFIG`: Path to the `blossomtune.yaml` file for UI text.
* `SPACE_ID`: The Hugging Face Space ID (e.g., `ethicalabs/BlossomTune-Orchestrator`). Used for auth.
* `SQLALCHEMY_URL`: The database connection string. Defaults to SQLite in the `data/db` volume.
* `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`: Credentials for the email sending service. Defaults to the local MailHog container.
* `EMAIL_PROVIDER`: Set to `mailjet` to use the Mailjet API instead of SMTP.
* `SUPERLINK_MODE`: `internal` (default) or `external`. In `internal` mode, the app starts its own Superlink. In `external` mode, it assumes one is running at `SUPERLINK_HOST`.
* `SUPERLINK_HOST`: Hostname of the Superlink (e.g., `host.docker.internal` when running in Docker).
* `TLS_CERT_DIR`: Path to the TLS certificate directory (defaults to `data/certs`).
* `AUTH_KEYS_DIR`: Path to the participant auth keys directory (defaults to `data/keys`).
* `FLOWER_APPS`: Comma-separated list of Python modules to load as Flower Apps (e.g., `flower_apps.quickstart_huggingface`).

## UI Text Configuration

All user-facing text in the Gradio UI can be modified without changing the Python code.

* **File**: `blossomtune_gradio/settings/blossomtune.yaml`
* **Schema**: `blossomtune_gradio/settings/blossomtune.schema.json`

This file contains key-value pairs for all messages, labels, and markdown content. It supports Jinja2 templating for dynamic values (e.g., `{{ participant_id }}`). See the developer guide for more details.

## Database Migrations

The application uses Alembic to manage database schema changes.

* **Config**: `alembic.ini`
* **Migrations**: `alembic/versions/`

By default, migrations are run automatically on startup (`RUN_MIGRATIONS_ON_STARTUP=true`). You can disable this and run them manually using standard Alembic commands.