import os
import yaml
import json
from typing import Any, Dict
from jsonschema import validate, ValidationError
from jinja2 import Template

from blossomtune_gradio import config as cfg


class Settings:
    """Handles loading and validation of UI text from a YAML file."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Settings, cls).__new__(cls)
        return cls._instance

    @classmethod
    def _reset_instance_for_testing(cls):
        """
        Resets the singleton instance.
        This method should ONLY be used in tests.
        """
        cls._instance = None

    def __init__(self, config_path: str | None = None, schema_path: str | None = None):
        """
        Initializes the settings object.
        The initialization logic runs only once per instance lifecycle.
        """
        # Use an instance-level flag to prevent re-initialization.
        if hasattr(self, "_initialized_instance"):
            return

        module_dir = os.path.dirname(__file__)

        # Always initialize attributes to ensure the object is in a consistent state.
        self.templates: Dict[str, Template] = {}
        # Prioritize env var, then passed arg, then default
        self.config_path = (
            cfg.BLOSSOMTUNE_CONFIG
            or config_path
            or os.path.join(module_dir, "blossomtune.yaml")
        )
        self.schema_path = schema_path or os.path.join(
            module_dir, "blossomtune.schema.json"
        )

        # Load the configuration.
        self._load_config()

        # Mark this specific instance as initialized.
        self._initialized_instance = True

    def _load_config(self) -> bool:
        """
        Loads YAML config, validates it, and compiles Jinja2 templates.
        This method populates self.templates on success or prints errors on failure.
        Returns True on success, False on any failure.
        """
        # Check for and validate the main config file
        try:
            with open(self.config_path, "r") as f:
                # safe_load can return None for an empty file, which is not an error itself
                config = yaml.safe_load(f)
                # If the file is not empty but safe_load returns None, it's invalid YAML
                if config is None and os.fstat(f.fileno()).st_size > 0:
                    raise yaml.YAMLError("Contains non-YAML content.")
        except FileNotFoundError:
            print(f"Error: Configuration file not found at {self.config_path}")
            return False
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")
            return False

        # Check for and validate the schema file
        try:
            with open(self.schema_path, "r") as f:
                schema = json.load(f)
        except FileNotFoundError:
            print(f"Error: JSON schema not found at {self.schema_path}")
            return False
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON schema: {e}")
            return False

        # Validate the config against the schema
        try:
            # The config can be None if the YAML file was empty.
            validate(instance=config, schema=schema)
        except ValidationError as e:
            print(f"Error: YAML configuration is invalid. {e.message}")
            return False

        # If everything is valid, compile the templates
        if config:
            ui_config = config.get("ui", {})
            for key, value in ui_config.items():
                if isinstance(value, str):
                    self.templates[key] = Template(value)

        return True

    def get_text(self, key: str, **kwargs: Any) -> str:
        """Renders a Jinja2 template with the given context."""
        if key in self.templates:
            return self.templates[key].render(**kwargs)
        return f"Warning: Text for '{key}' not found."


# Singleton instance that runs on first import.
# The _reset_instance_for_testing method is for isolating tests from this initial state.
settings = Settings()
