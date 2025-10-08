from blossomtune_gradio import config as cfg
from blossomtune_gradio.gradio_app import demo


if __name__ == "__main__":
    if cfg.RUN_MIGRATIONS_ON_STARTUP:
        database.run_migrations()
    demo.launch()
