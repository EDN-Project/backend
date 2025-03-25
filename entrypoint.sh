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

if [[ "$DB_EXIST" != "1" ]]; then
  echo "📌 Database 'eden' not found. Creating it..."
  psql -h db -U postgres -c "CREATE DATABASE eden;"
  echo "✅ Database 'eden' created successfully!"
fi

# Check if schema 'sensor_readings' exists
SCHEMA_EXIST=$(psql -h db -U postgres -d eden -tAc "SELECT 1 FROM information_schema.schemata WHERE schema_name='sensor_readings';")

if [[ "$SCHEMA_EXIST" == "1" ]]; then
  echo "⚠️ Schema 'sensor_readings' found. Skipping restore to preserve data."
else
  echo "📌 Schema 'sensor_readings' not found. Proceeding with backup restore..."
  pg_restore --verbose --clean --if-exists --no-owner --exit-on-error -h db -U postgres -d eden /app/eden.backup

  if [ $? -eq 0 ]; then
    echo "✅ Backup restored successfully!"
  else
    echo "⚠️ Backup restoration failed!"
  fi
fi

# Start the application
exec python /app/global_analysis.py
