# Project Structure

This document outlines the main components of the BlossomTune Orchestrator codebase.

```
.
├── alembic  # Alembic database migrations
├── alembic.ini  # Alembic config
├── blossomtune_gradio  # Main Python package
│   ├── __main__.py  # Entrypoint: runs migrations, launches app
│   ├── auth_keys.py  # Generates EC keys, builds authorized_keys.csv
│   ├── blossomfile.py  # Creates the .blossomfile zip archive
│   ├── config.py  # Loads configuration from environment variables
│   ├── database.py  # SQLAlchemy models (Request, Config)
│   ├── federation.py  # Core logic for join/approve/deny workflow
│   ├── generate_tls.py  # Logic for generating TLS certificates
│   ├── gradio_app.py  # Gradio App Logic 
│   ├── logs.py  # In-memory log handler for the UI
│   ├── mail.py  # Email sending logic (SMTP, Mailjet)
│   ├── processing.py  # Starts/stops Superlink/Runner subprocesses
│   ├── settings  # UI text config (YAML) and schema (JSON)
│   ├── tls.py  # In-memory log handler for the UI
│   ├── ui  # Gradio UI definitions
│   │   ├── auth.py  # Gradio auth handlers
│   │   ├── callbacks.py  # Gradio event handlers
│   │   ├── components.py # Gradio component definitions
│   └── util.py  # Misc utils
├── docker_entrypoint.sh  # Docker Entrypoint
├── docker-compose.yaml  # Docker Compose File
├── Dockerfile  # Docker Container File
├── docs  # This documentation
├── flower_apps  # Flower Apps
│   └── quickstart_huggingface  # Example Flower App
├── tests  # Tests (PyTest) 
```