#!/bin/sh
export PYTHONUNBUFFERED=1

REDIS_URL=${REDIS_URL:-redis://redis}
until redis-cli -u "$REDIS_URL" ping > /dev/null; do
    sleep 0.2
done

if [ -z "$CLEANUP_DISABLED"]; then
    python -m CHAD cleanup &
fi

if [ -n "$DEBUG" ]; then
    FLASK_ENV=development exec python -m CHAD serve
else
    exec gunicorn 'CHAD:app' \
        --bind '[::]:80' \
        --workers "$WORKERS" \
        --worker-class gevent
fi
