---
title: BlossomTune Flower Superlink
emoji: 🌸
colorFrom: pink
colorTo: purple
sdk: gradio
sdk_version: "5.44.1"
app_file: blossomtune_gradio/__main__.py
pinned: false
hf_oauth: true
---

# BlossomTune 🌸 Flower Superlink & Runner Orchestrator

Welcome to BlossomTune\! This application provides a comprehensive web-based orchestrator for managing federated learning (FL) experiments using Flower and Gradio.

It serves as a central control plane for administrators to manage the federation's infrastructure and for participants to securely join and receive their configurations.

## Project Overview

BlossomTune is designed to simplify the operational aspects of federated learning.

It provides a user-friendly interface that abstracts away the complexities of starting, monitoring, and managing the components of a Flower-based FL system.

The system manages a participant onboarding workflow, from initial request to admin approval, and provides the necessary connection details for approved participants to join the federated training process.

The project comes bundled with a sample federated learning application, `quickstart-huggingface`, which fine-tunes a `bert-tiny` model on the IMDB sentiment analysis dataset.

## Features

  * **Federated Learning Control**: Administrators can start and stop the core Flower `Superlink` and `Runner` processes directly from the UI.
  * **Participant Onboarding**: A dedicated tab allows new participants to request to join the federation by authenticating with their Hugging Face account and providing a contact email.
  * **Admin Panel**: A secure admin panel allows federation owners to review pending requests, approve or deny participants, and assign them to specific data partitions.
  * **Live Monitoring**: Provides a live, auto-scrolling log feed from the backend processes (`Superlink` and `Runner`) for real-time monitoring.
  * **Dynamic Configuration**: The system dynamically provides approved participants with the necessary connection details, their unique partition ID, and example commands to connect their client node.

## Setup and Installation

### Prerequisites

  * Python 3.11
  * Git

### Installation Steps

1.  **Clone the Repository**:

    ```bash
    git clone https://github.com/ethicalabs-ai/BlossomTune-Gradio.git
    cd BlossomTune-Flower-Superlink
    ```

2.  **Install Dependencies**:
    The project dependencies are defined in `pyproject.toml`. Install them using pip:

    ```bash
    pip install -e .
    ```

    This will install Gradio, Flower, Transformers, PyTorch, and other necessary packages.

3.  **(Optional) Setup Pre-commit Hooks**:
    This project uses `ruff` for code formatting and linting, managed via pre-commit hooks. To enable this, install pre-commit and set up the hooks:

    ```bash
    pip install pre-commit
    pre-commit install
    ```

## How to Run the Application

Launch the Gradio web interface by running:

```bash
python -m blossomtune_gradio
```

The application will be accessible via a local URL provided by Gradio.

## Generating Self-Signed Certificates for Local Development (Docker)

When running the application with `docker-compose`, the `superlink` service requires TLS certificates to enable secure connections.

For local development, you can generate a self-signed Certificate Authority (CA) and a `localhost` certificate using the provided script.

**Step 1: Run the Certificate Generator**

Execute the interactive TLS generation script located in the `blossomtune_gradio` directory:

```bash
python3 -m blossomtune_gradio.generate_tls
```

**Step 2: Choose the Development Option**

When prompted, select option **1** to generate a self-signed certificate for `localhost`.

```text
===== BlossomTune TLS Certificate Generator =====
Select an option:
  1. Generate a self-signed 'localhost' certificate (for Development)
  2. Generate a server certificate using the main CA (for Production)
  3. Exit
Enter your choice [1]: 1
```

The script will create a new directory named `certificates_localhost` containing the generated CA (`ca.crt`) and the server certificate files (`server.key`, `server.crt`, `server.pem`).

**Step 3: Copy Certificates to the Data Directory**

The `docker-compose.yml` file is configured to mount a local `./data/certs` directory into the `superlink` container. You must copy the essential certificate files into this location:

```bash
cp certificates_localhost/ca.crt ./data/certs/
cp certificates_localhost/server.key ./data/certs/
cp certificates_localhost/server.pem ./data/certs/
```

Once these files are in place, you can start the services using `docker compose up`.

The Superlink will automatically find and use these certificates to secure its connections.


## Usage Guide

### For Participants

1.  **Navigate to the "Join Federation" tab**.
2.  **Log in** using your Hugging Face account. On a Hugging Face Space, this is done via the login button.
3.  **Enter your contact email** and submit your request.
4.  You will receive an email with an **activation code**.
5.  Return to the "Join Federation" tab, enter the activation code, and submit it to activate your request.
6.  Once submitted and activated, your request will be **pending administrator review**. You can check your status on the same page.
7.  If **approved**, you will see the Superlink connection address and your assigned data partition ID, which you will use to configure your Flower client.

### For Administrators

1.  **Log in** with the Hugging Face account designated as the `SPACE_OWNER`. When running locally, admin controls are enabled by default.
2.  Navigate to the **"Admin Panel"** tab.
3.  **Start the Infrastructure**:
      * Click the "Start Superlink" button to launch the Flower Superlink process. Its status will change to "Running".
      * Select a "Runner App" (e.g., `flower_apps.quickstart_huggingface`), provide a "Run ID", and set the "Total Partitions".
      * Click "Start Federated Run" to launch the Flower Runner, which executes the federated learning strategy defined in the server app.
4.  **Manage Participant Requests**:
      * View pending requests in the "Pending Requests" table.
      * Click on a row to select a participant. Their ID will populate the management form, and a new partition ID will be suggested.
      * Click "Approve" or "Deny" to manage the request.

## Project Structure

The codebase is organized into two main packages: `blossomtune_gradio` (the web application) and `flower_apps` (the federated learning tasks).

```
└── BlossomTune-Gradio/
    ├── pyproject.toml              # Project metadata and dependencies for the orchestrator
    ├── .pre-commit-config.yaml     # Configuration for pre-commit hooks (ruff)
    ├── blossomtune_gradio/
    │   ├── __main__.py             # Makes the package runnable
    │   ├── config.py               # Application configuration from environment variables
    │   ├── database.py             # SQLite database initialization and schema
    │   ├── federation.py           # Logic for participant onboarding and management
    │   ├── gradio_app.py           # Defines the main Gradio UI layout and structure
    │   ├── processing.py           # Handles starting/stopping backend Flower processes
    │   └── ui/
    │       ├── auth.py             # Authentication logic (checks for space owner)
    │       ├── callbacks.py        # Callback functions for Gradio UI events
    │       └── components.py       # Reusable Gradio UI components
    └── flower_apps/
        └── quickstart_huggingface/
            ├── pyproject.toml      # Dependencies and config for this specific Flower app
            └── huggingface_example/
                ├── client_app.py   # Defines the Flower ClientApp
                ├── server_app.py   # Defines the Flower ServerApp
                └── task.py         # Defines the ML model, data loading, training, and evaluation
```