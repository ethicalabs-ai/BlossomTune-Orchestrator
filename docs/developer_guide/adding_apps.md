# How-To: Add a Flower App

The orchestrator can run any Flower App that is structured as a Python module. The `quickstart_huggingface` app is provided as an example.

## Steps to Add a New App

1.  **Create a New App Directory**

    Create a new directory under `flower_apps/`. The directory name should be a valid Python package name (e.g., `my_fl_project`).

    ```bash
    mkdir flower_apps/my_fl_project
    ```

2.  **Create Your Flower App**

    Inside your new directory, create the necessary files for a Flower App. The minimum requirement is a `client_app.py` and a `server_app.py` that define a `ClientApp` and `ServerApp` respectively.

    * `flower_apps/my_fl_project/client_app.py`:
        ```python
        from flwr.client import ClientApp
        # ... your client logic ...
        app = ClientApp(client_fn=...)
        ```

    * `flower_apps/my_fl_project/server_app.py`:
        ```python
        from flwr.server import ServerApp
        # ... your server logic ...
        app = ServerApp(server_fn=...)
        ```

    * You will also likely need an `__init__.py` and other files for your ML task, strategy, etc.

3.  **Define Dependencies (Optional)**

    If your app has specific Python dependencies, add a `pyproject.toml` or `requirements.txt` in your app's directory. The main `Dockerfile` does not automatically install these; you would need to modify it or ensure they are included in the base project's `pyproject.toml`.

4.  **Register the App**

    The orchestrator finds apps via the `FLOWER_APPS` environment variable. Add the Python module path of your new app to this list.

    You can set this in your `docker-compose.yaml`:

    ```yaml
    services:
      gradio_app:
        environment:
          FLOWER_APPS: "flower_apps.quickstart_huggingface,flower_apps.my_fl_project"
    ```

    Or in `blossomtune_gradio/config.py`:

    ```python
    FLOWER_APPS = os.getenv("FLOWER_APPS", [
        "flower_apps.quickstart_huggingface",
        "flower_apps.my_fl_project"
    ])
    ```

5.  **Restart and Run**

    After restarting the `gradio_app` container, your new app **"my_fl_project"** will appear in the **"Select Runner App"** dropdown in the Admin Panel.