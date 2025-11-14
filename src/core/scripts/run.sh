#!/bin/bash

set -e

RUN_MODE="${RUN_MODE}"
echo "RUN_MODE: $RUN_MODE"

if [ "$RUN_MODE" == "worker" ]; then
    echo "Starting in Worker Mode"
    WORKER=1 exec celery -A report worker -E -l INFO

elif [ "$RUN_MODE" == "worker-reload" ]; then
    echo "Starting in Worker Reload Mode"
    python ./manage.py runcelery

elif [ "$RUN_MODE" == "beat" ]; then
    echo "Starting in Beat Mode"
    WORKER=1 exec celery -A report beat -l INFO

elif [ "$RUN_MODE" == "listener" ]; then
    echo "Starting Listener $2"
    python manage.py broker_receiver --queue-name=$2

elif [ "$RUN_MODE" == "flower" ]; then
    echo "Starting in Flower Mode"
    exec celery -A report flower --basic_auth=${FLOWER_USERNAME}:${FLOWER_PASSWORD}

elif [ "$RUN_MODE" == "dev" ]; then
    echo "Starting in Development Mode"
    exec tail -f /dev/null

elif [ "$RUN_MODE" == "debug" ]; then
    echo "Starting in Debug Mode"
    debugpy --wait-for-client --listen 0.0.0.0:5678 manage.py runserver 0.0.0.0:8000 --nothreading --noreload

elif [ "$RUN_MODE" == "local" ]; then
    echo "Starting in Local Mode"
    python manage.py runserver 0.0.0.0:8000

else
    echo "Starting in Production mode"
    python manage.py migrate
    python manage.py collectstatic --no-input --clear
    daphne -b 0.0.0.0 -p 8000 report.asgi:application

fi