#!/bin/bash
set -e

# Initialize database tables
echo "Initializing database..."
python -c "from db.database import init_db; init_db()"

# Run the main command
echo "Starting StoryBot..."
exec "$@"
