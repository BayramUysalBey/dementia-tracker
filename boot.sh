#!/bin/sh
set -e

# --- 1. WAIT FOR DATABASE ---
python -c "
import socket
import time
import os
from urllib.parse import urlparse

# Try to get host from POSTGRES_HOST, then DATABASE_URL, then default to 'db'
db_url = os.environ.get('DATABASE_URL', '')
parsed_url = urlparse(db_url)
host = os.environ.get('POSTGRES_HOST', parsed_url.hostname or 'db')
port = int(os.environ.get('POSTGRES_PORT', parsed_url.port or 5432))

print(f'Checking connectivity to Postgres at {host}:{port}...')

# Limit the wait time in production so Render doesn't timeout the port scan
max_retries = 30 if os.environ.get('FLASK_DEBUG') == '0' else 100
retries = 0

while retries < max_retries:
    try:
        s = socket.create_connection((host, port), timeout=5)
        s.close()
        print('Postgres is READY.')
        break
    except (socket.error, ValueError):
        retries += 1
        print(f'({retries}/{max_retries}) Waiting for Postgres at {host}:{port}...')
        time.sleep(1)
else:
    print('Could not connect to Postgres. Starting app anyway and letting Flask handle errors.')
"

# --- 2. RUN MIGRATIONS ---
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."
	# Note: If this fails with a Redis ValueError, ensure REDIS_URL is set in Render.
    flask db upgrade
fi

# --- 3. START SERVICE ---
exec "$@"