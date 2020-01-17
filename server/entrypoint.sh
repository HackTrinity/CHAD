#!/bin/sh
exec gunicorn 'CHAD:app' \
    --bind '[::]:80' \
    --workers "$WORKERS" \
    --worker-class gevent
