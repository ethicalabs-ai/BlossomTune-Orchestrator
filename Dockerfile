# This stage installs uv and builds the Python virtual environment.
FROM python:3.11-slim AS builder

# Install uv - a fast Python package installer
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/

# Set the working directory
WORKDIR /app

# Create a virtual environment to keep dependencies isolated
RUN uv venv

# Explicitly set the virtual environment for subsequent commands.
# This helps ensure commands correctly locate the venv.
ENV VIRTUAL_ENV="/app/.venv"

# Copy dependency definition files
COPY pyproject.toml uv.lock ./

# Install dependencies into the virtual environment using uv
# This is faster than pip and uses the lock file for reproducible builds.
RUN uv sync --locked --no-cache --index-strategy=unsafe-best-match


# This stage creates the final, lean image for production.
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Consolidate ENV declarations for clarity and to avoid duplicate paths.
ENV PYTHONUNBUFFERED=1 \
    GRADIO_ALLOW_FLAGGING=never \
    GRADIO_NUM_PORTS=1 \
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_THEME=huggingface \
    SYSTEM=spaces \
    PYTHONUNBUFFERED=1 \
    # Add the virtual environment to the PATH
    PATH="/app/.venv/bin:$PATH"

# Set the working directory
WORKDIR /app

COPY --from=builder /usr/local/bin/uv /usr/local/bin/

# Copy the virtual environment from the builder stage. It now contains all dependencies.
ENV VIRTUAL_ENV="/app/.venv"
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Copy your application code into the image
# Using .dockerignore prevents unnecessary files from being copied.
COPY . .

# Expose the necessary ports
EXPOSE 9092
EXPOSE 7860

# Ensure PYTHONPATH for flower_apps
ENV PYTHONPATH="${PYTHONPATH}:/app/"

# Define the entrypoint and default command for the container
ENTRYPOINT ["/app/docker_entrypoint.sh"]
CMD ["gradio_app"]