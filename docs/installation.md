# Installation

BlossomTune is designed to be run as a set of Docker containers.

The recommended way to install and run the application is by using `docker compose`.

## Prerequisites

* Docker
* Docker Compose
* Git (for cloning the repository)
* Python 3.11 (for development)

## Running with Docker Compose

1.  **Clone the Repository**

    ```bash
    git clone [https://github.com/ethicalabs-ai/BlossomTune-Orchestrator.git](https://github.com/ethicalabs-ai/BlossomTune-Orchestrator.git)
    cd BlossomTune-Orchestrator
    ```

2.  **Set Environment Variables**

    The `docker-compose.yaml` file requires certain environment variables. The most important one is `HF_TOKEN` if you are deploying on Hugging Face Spaces.

    Export the environment variable `HF_TOKEN`:

    ```bash
    export HF_TOKEN=your_huggingface_token_here
    ```

3.  **Build and Run the Containers**

    This command will build the `blossomtune-orchestrator` image from the `Dockerfile` and start the `gradio_app`, `superlink`, and `mailhog` services.

    ```bash
    docker compose up --build
    ```

    * The **Gradio UI** will be available at `http://localhost:7860`.
    * The **MailHog UI** (for catching activation emails locally) will be at `http://localhost:8025`.
    * The **Flower Superlink** will be exposed on ports `9092` (SuperNode connections) and `9093` (Flower CLI).

4.  **Data Persistence**

    The `docker-compose.yaml` file is configured to mount local directories for persistent data:

    * `./data/db`: SQLite database
    * `./data/certs`: TLS certificates
    * `./data/keys`: Participant authentication keys
    * `./data/results`: Federated learning run artifacts