#!/bin/sh
if [ -n "$DEBUG" ]; then
    exec python -u -m CHAD
else
    exec gunicorn 'CHAD:app' \
        --bind '[::]:80' \
        --workers "$WORKERS" \
        --worker-class gevent
fi
