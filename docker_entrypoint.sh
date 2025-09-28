#!/bin/bash

set -e

echo "Env vars:"
env | grep -v -E "SECRET|KEY|TOKEN|PASSWORD|ACCESS"

if [ "${1}" = "gradio_app" ]; then
    echo "Running Gradio App..."
    exec python3 -m blossomtune_gradio
elif [ "${1}" = "superlink" ]; then
    echo "Running Superlink..."
    exec flower-superlink \
        --ssl-ca-certfile /data/certs/ca.crt \
        --ssl-certfile /data/certs/server.pem \
        --ssl-keyfile /data/certs/server.key
else
    exec "$@"
fi
