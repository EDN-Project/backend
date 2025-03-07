#!/bin/bash

echo "⏳ Waiting for PostgreSQL to be ready..."
export PGPASSWORD="ahmed2003"

# Wait until PostgreSQL is ready
until pg_isready -h db -p 5432 -U postgres; do
  echo "⌛ PostgreSQL is still loading..."
  sleep 2
done

echo "✅ PostgreSQL is ready!"

# Check if the database exists
DB_EXIST=$(psql -h db -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname='eden'")

if [[ "$DB_EXIST" == "1" ]]; then
  echo "⚠️ Database 'eden' already exists. Dropping it..."
  
  # Terminate active connections
  psql -h db -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='eden';"
  
  # Drop the database
  psql -h db -U postgres -c "DROP DATABASE eden;"
  echo "✅ Database 'eden' dropped successfully!"
fi

# Create the database again
echo "📌 Creating database 'eden'..."
psql -h db -U postgres -c "CREATE DATABASE eden;"
echo "✅ Database 'eden' created successfully!"

# Restore the backup
echo "📌 Restoring backup..."
pg_restore --verbose --clean --if-exists --no-owner --exit-on-error -h db -U postgres -d eden /app/eden.backup

if [ $? -eq 0 ]; then
  echo "✅ Backup restored successfully!"
else
  echo "⚠️ Backup restoration failed!"
fi

# Start the application
exec python /app/global_analysis.py
