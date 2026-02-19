#!/bin/bash
set -e

# Run migrations if this is the backend web service
if [ "$SERVICE_TYPE" = "backend" ]; then
    echo "Running database migrations..."
    alembic upgrade head
fi

# Execute the passed command
exec "$@"
