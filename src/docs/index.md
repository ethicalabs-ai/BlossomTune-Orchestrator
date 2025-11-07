# BlossomTune Orchestrator

![Python Version](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-Apache_2.0-green)

BlossomTune is a web-based orchestrator for managing Flower federated learning experiments.

It provides a Gradio-based user interface for both administrators and participants, simplifying the process of joining, managing, and running federated learning tasks.

The system is designed to be deployed via Docker and includes components for:

* **Participant Management**: A workflow for participants to request access, verify via email, and get approved by an administrator.
* **Federation Control**: Admin controls to start and stop the Flower Superlink and the Flower Runner processes.
* **Security**: Automated generation and management of TLS certificates and participant-specific authentication keys.
* **Dynamic Configuration**: A customizable UI text and settings system.

## Key Features

* **Gradio Web Interface**: A simple, interactive UI for all user roles.
* **Dockerized Services**: Easy deployment using `docker compose` for the `gradio_app`, `superlink`, and `mailhog` services.
* **Secure Federation**: Built-in TLS and EC key-pair authentication for participants.
* **`Blossomfile` Generation**: Approved participants receive a simple `.zip` file with all necessary keys and configuration to join.
* **Pluggable Flower Apps**: Easily add new federated learning tasks by dropping them into the `flower_apps/` directory.
* **Database Persistence**: Uses SQLite with Alembic migrations to store participant status and application configuration.

## Notes

Please note that due to HF networking and security limitations, you cannot run a Superlink server using Huggingface Spaces.

Authentication keys and certs that are generated on HF will need to be synced manually via SSH to your Bare Metal or Cloud VM.

An installation guide for Bare Metal Linux will be provided.