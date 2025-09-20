import pytest
import yaml
import json
from unittest.mock import patch

# Import the Settings class specifically to allow for instance management in tests
from blossomtune_gradio.settings import Settings


@pytest.fixture(autouse=True)
def reset_settings_singleton():
    """
    Fixture to automatically reset the Settings singleton before each test.
    This allows creating a new, clean instance for each test scenario by
    directly resetting the internal `_instance` variable.
    """
    Settings._instance = None


@pytest.fixture
def valid_config_files(tmp_path):
    """Creates a valid config and schema file in a temporary directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    config_content = {
        "ui": {
            "welcome_message_md": "Hello, {{ name }}!",
            "error_message_md": "An error occurred.",
        }
    }
    schema_content = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "ui": {
                "type": "object",
                "properties": {
                    "welcome_message_md": {"type": "string"},
                    "error_message_md": {"type": "string"},
                },
                "required": ["welcome_message_md", "error_message_md"],
            }
        },
        "required": ["ui"],
    }

    config_path = config_dir / "blossomtune.yaml"
    schema_path = config_dir / "blossomtune.schema.json"

    with open(config_path, "w") as f:
        yaml.dump(config_content, f)
    with open(schema_path, "w") as f:
        json.dump(schema_content, f)

    return str(config_path), str(schema_path)


def test_load_valid_config(valid_config_files):
    """Tests successful loading of a valid configuration."""
    config_path, schema_path = valid_config_files
    settings = Settings(config_path=config_path, schema_path=schema_path)

    assert "welcome_message_md" in settings.templates
    assert "error_message_md" in settings.templates

    rendered_text = settings.get_text("welcome_message_md", name="World")
    assert rendered_text == "Hello, World!"


def test_missing_config_file(tmp_path, capsys):
    """Tests handling of a missing configuration file and captures stdout."""
    schema_path = tmp_path / "schema.json"
    schema_path.touch()  # Create an empty schema for the test
    settings = Settings(config_path="nonexistent.yaml", schema_path=str(schema_path))

    assert not settings.templates

    # Check that an error was printed to the console
    captured = capsys.readouterr()
    assert "Error: Configuration file not found" in captured.out


def test_invalid_yaml_file(tmp_path, capsys):
    """Tests handling of a syntactically incorrect YAML file."""
    config_path = tmp_path / "invalid.yaml"
    schema_path = tmp_path / "schema.json"
    schema_path.touch()

    with open(config_path, "w") as f:
        f.write("ui: { welcome: 'Hello'")  # Malformed YAML

    settings = Settings(config_path=str(config_path), schema_path=str(schema_path))
    assert not settings.templates
    captured = capsys.readouterr()
    assert "Error parsing YAML file" in captured.out


def test_schema_validation_failure(tmp_path, capsys):
    """Tests that validation fails if the config doesn't match the schema."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Config is missing the required 'error_message'
    config_content = {"ui": {"welcome_message_md": "Hello!"}}
    schema_content = {
        "type": "object",
        "properties": {"ui": {"type": "object", "required": ["error_message_md"]}},
    }

    config_path = config_dir / "blossomtune.yaml"
    schema_path = config_dir / "blossomtune.schema.json"

    with open(config_path, "w") as f:
        yaml.dump(config_content, f)
    with open(schema_path, "w") as f:
        json.dump(schema_content, f)

    settings = Settings(config_path=str(config_path), schema_path=str(schema_path))
    assert not settings.templates
    captured = capsys.readouterr()
    assert "Error: YAML configuration is invalid" in captured.out


@patch("blossomtune_gradio.config.BLOSSOMTUNE_CONFIG")
def test_load_from_env_variable(mock_config_env, valid_config_files):
    """Tests loading the config path from an environment variable."""
    config_path, schema_path = valid_config_files
    mock_config_env = config_path

    # By patching the config module, the Settings constructor will pick it up
    with patch("blossomtune_gradio.settings.cfg.BLOSSOMTUNE_CONFIG", mock_config_env):
        settings = Settings(schema_path=schema_path)

    assert settings.config_path == config_path
    rendered_text = settings.get_text("welcome_message_md", name="From Env")
    assert rendered_text == "Hello, From Env!"


def test_singleton_pattern(valid_config_files):
    """Tests that the same instance of Settings is always returned."""
    config_path, schema_path = valid_config_files
    s1 = Settings(config_path=config_path, schema_path=schema_path)
    s2 = Settings()  # Should return the same instance as s1

    assert s1 is s2
    # Verify s2 is configured, proving it's the same instance
    assert "welcome_message_md" in s2.templates
