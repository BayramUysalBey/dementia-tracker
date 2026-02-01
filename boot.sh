#!/bin/sh
set -e

# --- 1. WAIT FOR DATABASE ---
# This robust Python script checks if the internal 'db' service is ready.
python -c "
import socket; 
import time; 
import os;

# The host is the name of the database service defined in docker-compose.yml
host = os.environ.get('POSTGRES_HOST', 'db')
port = 5432
while True:
    try:
        s = socket.create_connection((host, port), timeout=5)
        s.close()
        print('Postgres is READY.')
        break
    except socket.error:
        print(f'Waiting for Postgres at {host}:{port}...')
        time.sleep(1)
"

# --- 2. RUN MIGRATIONS (Alembic) ---
# Only run migrations if requested (prevents race conditions)
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."
    flask db upgrade
fi

# --- 3. START SERVICE ---
# Execute the command passed to the script (e.g., gunicorn or rq)
exec "$@"