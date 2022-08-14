#!/bin/bash

SERVER_ENV=$1

echo "Running server for env '$SERVER_ENV'"

if [[ "$SERVER_ENV" = "prod" ]]; then
    gunicorn 'app:app' --config gunicorn_config.py
else
    python3 app.py
fi
