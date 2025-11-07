# Contributing

Contributions are welcome! This project follows a standard fork-and-pull-request workflow.

## Development Setup

1.  Clone the repository.
2.  It is recommended to use a Python 3.11 virtual environment.
3.  Install the project in editable mode with development dependencies:
    ```bash
    pip install -e ".[dev]"
    ```
    This installs `pytest`, `ruff`, `pre-commit`, etc.

## Code Style and Linting

This project uses [Ruff](https://docs.astral.sh/ruff/) for all linting and formatting.

* **Linter**: `ruff-check`
* **Formatter**: `ruff-format`

Configuration is defined in the `[tool.ruff]` sections of `pyproject.toml`.

## Pre-commit Hooks

The repository includes a `.pre-commit-config.yaml` file to automatically run `ruff-check` and `ruff-format` on every commit.

To install the hooks:

```bash
pre-commit install
```

This ensures that all committed code adheres to the project's code style.

## Running Tests

Tests are written using pytest.

```bash
pytest
```

Test configuration is in the `[tool.pytest.ini_options]` section of `pyproject.toml`.


**BUILD COMMANDS:**
```bash
# Install documentation dependencies
pip install -r docs/requirements.txt

# Install the project itself (for mkdocstrings to find it)
pip install .

# Build the documentation site
mkdocs build

# Serve the documentation locally
mkdocs serve
# (Site will be available at http://127.0.0.1:8000)