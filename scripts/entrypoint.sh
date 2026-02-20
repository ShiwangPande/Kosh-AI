#!/bin/bash
set -e

# Run migrations if this is the backend web service
if [ "$SERVICE_TYPE" = "backend" ]; then
    echo "Running database migrations..."
    # Run alembic from the backend folder so it finds the 'alembic' directory
    (cd backend && alembic upgrade head)
    echo "Initializing admin user..."
    python scripts/init_admin.py
fi




# Execute the passed command
exec "$@"
