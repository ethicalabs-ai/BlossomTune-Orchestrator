#!/bin/bash

set -e

echo "Env vars:"
env | grep -v -E "SECRET|KEY|TOKEN|PASSWORD|ACCESS"

if [ "${1}" = "gradio_app" ]; then
    echo "Running Gradio App..."
    exec python3 -m blossomtune_gradio
else
    exec "$@"
fi
