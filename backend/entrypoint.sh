#!/bin/sh
set -e

if [ ! -f "migrations/env.py" ]; then
    echo "Initializing migrations..."
    flask db init
    flask db migrate -m "initial"
fi

echo "Running database upgrade..."
flask db upgrade

echo "Seeding default categories..."
flask seed-mcc

echo "Starting gunicorn..."
exec gunicorn -w 4 -b 0.0.0.0:5000 'app:create_app()'
