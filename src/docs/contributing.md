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